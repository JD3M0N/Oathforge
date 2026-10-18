"""Private achievement interaction and post-commit notification delivery."""
import logging
from html import escape
from sqlalchemy import select
from telegram.constants import ParseMode
from oathforge.bot import render
from oathforge.bot.handlers.common import edit_or_send, load
from oathforge.bot.keyboards import btn, cb, markup
from oathforge.database.models import Character, User
from oathforge.database.session import session_scope
from oathforge.services import achievements
from oathforge.i18n import t
from oathforge.content import get_content

log = logging.getLogger(__name__)


async def handle(update, context, arg="-", mutation=False, nonce="-"):
    async with session_scope() as session:
        user, char = await load(session, update, lock=mutation)
        lang = user.language
        if char is None:
            text, keyboard = t(lang, "start.need_character"), None
        else:
            error = None
            if mutation:
                parts = arg.split(":")
                if len(parts) not in (2, 3):
                    error, arg = "achievements.invalid", "-"
                else:
                    operation, key = parts[:2]
                    result = await achievements.preference(session, char, operation, key, nonce,
                                                           parts[2] if len(parts) == 3 else None)
                    arg = f"d:{key}" if key != "-" else "-"
                    if result.error == "achievements.full":
                        arg = f"replace:{operation}:{key}"
                    else:
                        error = result.error
            text, keyboard = await render.achievements_view(session, char, lang, arg)
            if error:
                text = t(lang, error) + "\n\n" + text
    await edit_or_send(update, text, keyboard)


async def deliver(bot, telegram_id, chat_id):
    """Called after the action handler returns and all its transactions have closed."""
    async with session_scope() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user is None:
            return
        char = await session.scalar(select(Character).where(Character.user_id == user.id))
        if char is None:
            return
        char_id, lang = char.id, user.language
        claimed = await achievements.claim_notification(session, char_id)
    if claimed is None:
        return
    token, keys = claimed
    catalog = get_content().achievements
    names = [escape(catalog[key].name.get(lang)) for key in keys if key in catalog]
    text = t(lang, "achievements.announcement", count=len(names)) + "\n" + " · ".join(names)
    delivered = False
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML,
                               reply_markup=markup([[btn(t(lang, "achievements.open"), cb("ach", "l:earned:0"))]]))
        delivered = True
    except Exception:
        log.warning("Achievement notification remains pending for character %s", char_id, exc_info=True)
    finally:
        async with session_scope() as session:
            await achievements.finish_notification(session, char_id, token, delivered)


async def deliver_update(update, context):
    """Registered in main.py after every other handler: any private update may announce pending feats."""
    if (update.effective_chat is not None and getattr(update.effective_chat, "type", None) == "private"
            and update.effective_user is not None):
        await deliver(context.bot, update.effective_user.id, update.effective_chat.id)
