"""/hero /sheet /inventory /journal /quests /roll /look /language /help."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from oathforge import __version__
from oathforge.bot import render
from oathforge.bot.handlers import callbacks
from oathforge.bot.handlers.common import current_view, load, send, send_photos
from oathforge.bot.keyboards import btn, cb, markup
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.i18n import t


def _view(builder):
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        async with session_scope() as session:
            user, char = await load(session, update)
            lang = context.user_data["lang"] = user.language
            if char is None:
                text, kb = t(lang, "start.need_character"), None
            else:
                text, kb = await builder(session, char, lang)
        await send(update, text, kb)
    return handle


async def sheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """The class portrait (when the class has one), then the full sheet below it."""
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = context.user_data["lang"] = user.language
        if char is None:
            text, kb = t(lang, "start.need_character"), None
        else:
            images = get_content().media.class_images(char.class_key, char.gender)
            if images:
                await send_photos(session, update, context, images, render.portrait_caption(char, lang))
            text, kb = await render.sheet(session, char, lang)
    await send(update, text, kb)


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = user.language
    kb = markup([[btn("🇪🇸 Español", cb("lang", "es")), btn("🇬🇧 English", cb("lang", "en"))]])
    await send(update, t(lang, "lang.choose"), kb)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = user.language
    await send(update, f'{t(lang, "help.text")}\n\n{t(lang, "help.version", version=__version__)}')


def handlers() -> list[CommandHandler]:
    return [
        CommandHandler("look", _view(current_view)),
        CommandHandler("hero", _view(render.hero)),
        CommandHandler("sheet", sheet),
        CommandHandler("inventory", _view(render.inventory_view)),
        CommandHandler("journal", _view(render.journal)),
        CommandHandler("quests", _view(render.missions)),
        CommandHandler("roll", callbacks.roll_command),
        CommandHandler("language", language),
        CommandHandler("help", help_cmd),
    ]
