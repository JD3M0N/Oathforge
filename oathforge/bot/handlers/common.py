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
from oathforge.bot.keyboards import btn, cb, markup, nonce
from oathforge.content import get_content
from oathforge.database.models import WorldActivity
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.services import characters, chronicles, combat_service, media
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


async def current_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The combat panel if fighting, otherwise the scene."""
    enc = await combat_service.active_encounter(session, char)
    if enc is not None:
        return render.combat_panel(char, enc.state, lang, version=enc.version)
    return await render.scene(session, char, lang)


def _record(update: Update, text: str, kb: InlineKeyboardMarkup | None, edited: bool) -> None:
    if update.effective_user is not None:
        buttons = [b.text for row in kb.inline_keyboard for b in row] if kb else []
        recorder.outgoing(update.effective_user.id, text, buttons, edited=edited)


async def send(update: Update, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    await update.effective_chat.send_message(text, parse_mode=ParseMode.HTML, reply_markup=kb,
                                             disable_web_page_preview=True)
    _record(update, text, kb, edited=False)


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


def schedule_ready_ping(update: Update, context: ContextTypes.DEFAULT_TYPE, char_id: int, seconds: int) -> None:
    """A heads-up when the activity just started is done. Best effort: the timer itself lives in the
    database, so a restart only loses this message, never the activity."""
    jobs = getattr(context, "job_queue", None)
    if jobs is None or update.effective_chat is None:
        return
    jobs.run_once(_ready_ping, when=seconds + 1, chat_id=update.effective_chat.id,
                  data={"char_id": char_id, "lang": context.user_data.get("lang", "es")})


async def _ready_ping(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    char_id, lang = job.data["char_id"], job.data["lang"]
    async with session_scope() as session:
        act = await session.scalar(select(WorldActivity).where(WorldActivity.character_id == char_id,
                                                               WorldActivity.status == "running"))
        if act is None or act.ends_at > time.time():  # collected, abandoned, or a newer activity
            return
        place = get_content().locations[act.location].name.get(lang)
    kb = markup([[btn(t(lang, "btn.claim"), cb("actc", "-", nonce()))]])
    try:
        await context.bot.send_message(job.chat_id, t(lang, "activity.ready_ping", place=escape(place)),
                                       parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:  # a heads-up only
        log.warning("could not send the activity ping", exc_info=True)


async def edit_or_send(update: Update, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    q = update.callback_query
    if q is not None and q.message is not None:
        try:
            await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb,
                                      disable_web_page_preview=True)
            _record(update, text, kb, edited=True)
            return
        except Exception:  # message too old / not modified: fall back to a new message
            pass
    await send(update, text, kb)


async def send_photos(session: AsyncSession, update: Update, context: ContextTypes.DEFAULT_TYPE,
                      assets: list[MediaAsset], caption: str) -> None:
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
    album = [InputMediaPhoto(p, caption=caption if i == 0 else None, parse_mode=ParseMode.HTML)
             for i, p in enumerate(photos)]
    return list(await chat.send_media_group(album))
