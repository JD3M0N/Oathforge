import asyncio
import random
import time
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Chat, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from oathforge import recorder
from oathforge.bot import render
from oathforge.database.models import Character, User
from oathforge.services import characters, combat_service

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
        return render.combat_panel(char, enc.state, lang)
    return await render.scene(session, char, lang)


def _record(update: Update, text: str, kb: InlineKeyboardMarkup | None, edited: bool) -> None:
    if update.effective_user is not None:
        buttons = [b.text for row in kb.inline_keyboard for b in row] if kb else []
        recorder.outgoing(update.effective_user.id, text, buttons, edited=edited)


async def send(update: Update, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    await update.effective_chat.send_message(text, parse_mode=ParseMode.HTML, reply_markup=kb,
                                             disable_web_page_preview=True)
    _record(update, text, kb, edited=False)


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
