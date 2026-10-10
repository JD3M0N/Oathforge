import random
import time

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

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


async def send(update: Update, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    await update.effective_chat.send_message(text, parse_mode=ParseMode.HTML, reply_markup=kb,
                                             disable_web_page_preview=True)


async def edit_or_send(update: Update, text: str, kb: InlineKeyboardMarkup | None = None) -> None:
    q = update.callback_query
    if q is not None and q.message is not None:
        try:
            await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb,
                                      disable_web_page_preview=True)
            return
        except Exception:  # message too old / not modified: fall back to a new message
            pass
    await send(update, text, kb)
