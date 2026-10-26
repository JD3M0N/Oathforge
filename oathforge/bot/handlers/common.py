import asyncio
import logging
from html import escape
import random
import time
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Chat, InlineKeyboardMarkup, InputMediaPhoto, Message, Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest, NetworkError
from telegram.ext import ContextTypes

from oathforge import recorder
from oathforge.bot import render
from oathforge.content.media import MediaAsset
from oathforge.database.models import Character, User
from oathforge.bot.keyboards import FIXED, KEYBOARD_VERSION, btn, cb, fixed_keyboard, markup, nonce
from oathforge.content import get_content
from oathforge.database.models import WorldActivity
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.services import activities, characters, chronicles, combat_service, media
from oathforge.services.events import Outcome

log = logging.getLogger(__name__)

MAX_CAPTION = 1024
MAX_ALBUM = 10

RATE_WINDOW = 6.0
RATE_MAX = 8


def rng() -> random.Random:
    return random.Random()


def rate_ok(context: ContextTypes.DEFAULT_TYPE, telegram_id: int) -> bool:
    """Sliding window limiter per user, shared across chats."""
    buckets = context.bot_data.setdefault("rate", {})
    now = time.monotonic()
    recent = [ts for ts in buckets.get(telegram_id, []) if now - ts < RATE_WINDOW]
    if len(recent) >= RATE_MAX:
        buckets[telegram_id] = recent
        return False
    buckets[telegram_id] = recent + [now]
    return True


@asynccontextmanager
async def keep_typing(chat: Chat):
    """Telegram drops the typing indicator after ~5 s; resend it while the AI is thinking."""

    async def loop():
        while True:
            try:
                await chat.send_action(ChatAction.TYPING)
            except Exception:  # cosmetic only
                pass
            await asyncio.sleep(4)

    task = asyncio.create_task(loop())
    try:
        yield
    finally:
        task.cancel()


async def load(session: AsyncSession, update: Update, lock: bool = False) -> tuple[User, Character | None]:
    tg = update.effective_user
    user = await characters.get_or_create_user(session, tg.id, tg.language_code)
    char = await characters.get_character(session, user.id, lock=lock)
    return user, char


async def current_view(
    session: AsyncSession, char: Character, lang: str, compact: bool = False
) -> tuple[str, InlineKeyboardMarkup]:
    """The combat panel if fighting, otherwise the scene (``compact``: only its heading, under a result)."""
    enc = await combat_service.active_encounter(session, char)
    if enc is not None:
        return render.combat_panel(char, enc.state, lang, version=enc.version)
    return await render.scene(session, char, lang, compact=compact)


async def offer_keyboard(update: Update, user: User, lang: str, force: bool = False) -> None:
    """The fixed keyboard (🧝 🗺 🎒 📖) once per language, so players who started before it get it too.
    Call it inside the session: it remembers that it was sent."""
    sent = f"{lang}:{KEYBOARD_VERSION}"
    if not force and (user.settings or {}).get("keyboard") == sent:
        return
    characters.set_setting(user, "keyboard", sent)
    text = t(lang, "kb.ready")
    await update.effective_chat.send_message(text, reply_markup=fixed_keyboard(lang))
    recorder.outgoing(update.effective_user.id, text, [t(lang, f"kb.{k}") for k in FIXED], edited=False)


def _record(update: Update, text: str, kb: InlineKeyboardMarkup | None, edited: bool) -> None:
    if update.effective_user is not None:
        buttons = [b.text for row in kb.inline_keyboard for b in row] if kb else []
        recorder.outgoing(update.effective_user.id, text, buttons, edited=edited)


async def send(update: Update, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    await update.effective_chat.send_message(
        text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True
    )
    _record(update, text, kb, edited=False)


_answered: set[str] = set()  # button presses already answered: Telegram shows only the first popup


async def answer(update: Update, text: str | None = None) -> None:
    """Stop the spinner on the pressed button, once. ``text`` shows as a small popup that leaves nothing in the
    chat (a refusal, a stale menu); without a button press (a command) it is sent as a message instead."""
    q = update.callback_query
    if q is None:
        if text:
            await send(update, escape(text))
        return
    if q.id in _answered:
        return
    _answered.add(q.id)
    try:
        await q.answer(text[:200] if text else None)
    except (BadRequest, NetworkError) as e:  # the spinner is decoration: carry on
        log.warning("could not answer a button press (%s)", type(e).__name__)


def answered(update: Update) -> None:
    """Forget the press once it is handled."""
    if update.callback_query is not None:
        _answered.discard(update.callback_query.id)


async def drop_buttons(update: Update) -> None:
    """The pressed message keeps its text but loses its buttons: the new message below carries them."""
    q = update.callback_query
    if q is not None and q.message is not None:
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except (BadRequest, NetworkError):  # already without buttons, or too old to edit
            pass


async def send_result(
    update: Update,
    outcome: Outcome,
    lang: str,
    view: str,
    kb: InlineKeyboardMarkup | None,
    narration: str | None = None,
) -> None:
    """What happened and the buttons to carry on, in one message: the result, each level gained as a card of
    its own, and the view (usually the scene's heading) at the end of the last one."""
    messages = [m for m in [render.outcome_text(outcome, lang, narration), *render.level_up_cards(outcome, lang)] if m]
    if messages and len(messages[-1]) + len(view) + 2 <= render.MAX_MESSAGE:
        messages[-1] += "\n\n" + view
    else:
        messages.append(view)
    await drop_buttons(update)
    for message in messages[:-1]:
        await send(update, message)
    await send(update, messages[-1], kb)


async def send_outcome(update: Update, outcome: Outcome, lang: str, narration: str | None = None) -> None:
    """Results as one bullet message, then each level gained as a card of its own."""
    text = render.outcome_text(outcome, lang, narration)
    if text:
        await send(update, text)
    for card in render.level_up_cards(outcome, lang):
        await send(update, card)


async def send_chronicle(update: Update, context: ContextTypes.DEFAULT_TYPE, activity_id: int, lang: str) -> None:
    """The expedition's chronicle (AI while the daily budget lasts, then a generic one), after the facts."""
    async with keep_typing(update.effective_chat):
        ch = await chronicles.tell(context.bot_data["llm"], activity_id, lang)
    if ch is not None:
        await send(update, f"{t(lang, 'chronicle.title')}\n\n<i>{escape(ch.text)}</i>\n\n{chronicles.footer(ch, lang)}")


class BotChat:
    """A private chat reached through the bot (no update to answer): the player may be offline."""

    def __init__(self, bot, chat_id: int):
        self.bot, self.id = bot, chat_id

    async def send_message(self, text: str, **kwargs):
        return await self.bot.send_message(self.id, text, **kwargs)


async def send_activity_result(
    chat,
    telegram_id: int,
    llm,
    outcome: Outcome,
    lang: str,
    view: tuple[str, InlineKeyboardMarkup | None] | None = None,
) -> None:
    """What a finished activity gave, with its chronicle, in one message; level-ups as their own cards.
    ``view``: the buttons to carry on (the scene's heading), at the end of the last message."""
    if outcome.activity_id:
        async with session_scope() as session:
            act = await session.get(WorldActivity, outcome.activity_id)
            skill = act.skill if act else ""
            title = render.activity_title(act, lang) if act else None
        async with keep_typing(chat):
            ch = await chronicles.tell(llm, outcome.activity_id, lang)
        text = render.activity_result(
            outcome, skill, lang, ch.text if ch else None, chronicles.footer(ch, lang) if ch else None, title
        )
    else:
        text = render.outcome_text(outcome, lang)
    messages = [m for m in [text, *render.level_up_cards(outcome, lang)] if m]
    kb = None
    if view is not None:
        kb = view[1]
        if messages and len(messages[-1]) + len(view[0]) + 2 <= render.MAX_MESSAGE:
            messages[-1] += "\n\n" + view[0]
        else:
            messages.append(view[0])
    for i, message in enumerate(messages):
        last = kb if i == len(messages) - 1 else None
        await chat.send_message(message, parse_mode=ParseMode.HTML, reply_markup=last, disable_web_page_preview=True)
        recorder.outgoing(
            telegram_id, message, [b.text for row in last.inline_keyboard for b in row] if last else [], edited=False
        )


async def finish_due_activities(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Every few seconds (JobQueue): activities whose time is up end by themselves, and the player gets the
    result even if Telegram is closed. The timer lives in the database, so a restart loses nothing."""
    async with session_scope() as session:
        due = await activities.due(session)
    for char_id in due:
        try:
            await _finish_one(context, char_id)
        except Exception:  # one player's problem never stops the others
            log.warning("could not finish the activity of character %s", char_id, exc_info=True)


async def _finish_one(context: ContextTypes.DEFAULT_TYPE, char_id: int) -> None:
    async with session_scope() as session:
        char = await session.scalar(select(Character).where(Character.id == char_id).with_for_update())
        if char is None:
            return
        user = await session.get(User, char.user_id)
        lang, telegram_id = user.language, user.telegram_id
        out = await activities.claim(session, char)  # locked and checked again: a button press can't pay twice
        if not out.ok:
            return
        view = await current_view(session, char, lang, compact=True)
    chat = BotChat(context.bot, telegram_id)
    await send_activity_result(chat, telegram_id, context.bot_data["llm"], out, lang, view)
    from oathforge.bot.handlers.achievements import deliver

    await deliver(context.bot, user.telegram_id, user.telegram_id)


async def edit_or_send(update: Update, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    q = update.callback_query
    if q is not None and q.message is not None:
        try:
            await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
            _record(update, text, kb, edited=True)
            return
        except BadRequest as e:
            if "not modified" in str(e).lower():  # the same view pressed again: it is already on screen
                return
        except Exception:  # message too old or deleted: fall back to a new message
            pass
    await send(update, text, kb)


async def send_photos(
    session: AsyncSession, update: Update, context: ContextTypes.DEFAULT_TYPE, assets: list[MediaAsset], caption: str
) -> None:
    """One photo, or an album of up to 10, reusing cached file_ids; caches the new ones."""
    bot_id, chat = context.bot.id, update.effective_chat
    assets = assets[:MAX_ALBUM]
    ids = [await media.get_file_id(session, bot_id, a) for a in assets]
    try:
        try:
            sent = await _send_photos(chat, assets, ids, caption[:MAX_CAPTION])
        except BadRequest:
            if not any(ids):
                raise
            for a, fid in zip(assets, ids):  # a cached file_id Telegram no longer accepts: upload again
                if fid:
                    await media.forget(session, bot_id, a)
            ids = [None] * len(assets)
            sent = await _send_photos(chat, assets, ids, caption[:MAX_CAPTION])
    except NetworkError as e:  # TimedOut included: images are decoration, the text view still follows
        if isinstance(e, BadRequest):
            raise
        log.warning("could not send %s: %s", ", ".join(a.key for a in assets), e)
        return
    for a, fid, msg in zip(assets, ids, sent):
        if fid is None and msg.photo:
            biggest = msg.photo[-1]
            await media.remember(session, bot_id, a, biggest.file_id, biggest.file_unique_id)
    if update.effective_user is not None:
        names = ", ".join(a.key for a in assets)
        recorder.outgoing(update.effective_user.id, f"[🖼️ {names}]\n{caption}")


async def _send_photos(chat: Chat, assets: list[MediaAsset], ids: list[str | None], caption: str) -> list[Message]:
    photos = [fid or a.path.read_bytes() for a, fid in zip(assets, ids)]
    if len(photos) == 1:
        return [await chat.send_photo(photos[0], caption=caption, parse_mode=ParseMode.HTML)]
    album = [
        InputMediaPhoto(p, caption=caption if i == 0 else None, parse_mode=ParseMode.HTML) for i, p in enumerate(photos)
    ]
    return list(await chat.send_media_group(album))
