"""/rulebook /lineage /background /hero /sheet /inventory /journal /quests /classes /class_<key> /report /professions /prof_<key> /settings /look
/map /language /help."""

import re

from telegram import Update
from telegram.ext import BaseHandler, CommandHandler, ContextTypes, MessageHandler, filters

from oathforge import __version__
from oathforge.bot import render
from oathforge.bot.handlers.common import current_view, load, send, send_photos
from oathforge.bot.keyboards import btn, cb, markup
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.i18n import t
from oathforge.services import combat_service


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


CLASS_LINK = re.compile(r"^/class_([a-z_]+?)(?:@\w+)?$")


async def classes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/classes lists every class; /class_<key> (tappable from the level-up card and the sheet) opens one."""
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = context.user_data["lang"] = user.language
    m = CLASS_LINK.match((update.message.text or "").strip()) if update.message else None
    text, kb = render.class_page(m.group(1), lang, char) if m else render.classes_list(lang)
    await send(update, text, kb)


async def rulebook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/rulebook: how the game works, section by section; no character needed."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = user.language
    await send(update, *render.rulebook(lang))


async def lineages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/lineage: also works halfway through character creation, to look before choosing."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = user.language
    await send(update, render.lineages_list(lang))


async def backgrounds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/background: every background, also during character creation."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = user.language
    await send(update, render.backgrounds_list(lang))


SKILL_LINK = re.compile(r"^/skill_([a-z_]+?)(?:@\w+)?$")


async def skill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/skill_<key>: a class ability in depth (tappable from /class_<key>, the level-up card and /sheet)."""
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = context.user_data["lang"] = user.language
    m = SKILL_LINK.match((update.message.text or "").strip()) if update.message else None
    await send(update, *render.skill_page(m.group(1) if m else "", lang, char))


PROF_LINK = re.compile(r"^/prof_([a-z_]+?)(?:@\w+)?$")


async def profession_guide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/prof_<key>: the mini guide of a profession or hobby (tappable from /professions)."""
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = context.user_data["lang"] = user.language
        m = PROF_LINK.match((update.message.text or "").strip()) if update.message else None
        text, kb = render.profession_page(m.group(1) if m else "", lang, char)
    await send(update, text, kb)


async def _report(session, char, lang):
    return render.report_page(await combat_service.battle_report(session, char), 0, lang)


async def _map(session, char, lang):
    """The map; during a fight, the combat panel (no walking away from it)."""
    if char.state == "in_combat":
        return await current_view(session, char, lang)
    return render.map_view(char, lang)


async def _professions(session, char, lang):
    return render.professions_view(char, lang)


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/settings: language and manual rolls."""
    async with session_scope() as session:
        user, _ = await load(session, update)
        lang = context.user_data["lang"] = user.language
        text, kb = render.settings_view(user, lang)
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


def handlers() -> list[BaseHandler]:
    return [
        CommandHandler("look", _view(current_view)),
        CommandHandler("map", _view(_map)),
        CommandHandler("hero", _view(render.hero)),
        CommandHandler("sheet", sheet),
        CommandHandler("inventory", _view(render.inventory_view)),
        CommandHandler("journal", _view(render.journal)),
        CommandHandler("quests", _view(render.missions)),
        CommandHandler(["rulebook", "rules"], rulebook),
        CommandHandler(["lineage", "race"], lineages),
        CommandHandler("background", backgrounds),
        CommandHandler("classes", classes),
        MessageHandler(filters.Regex(CLASS_LINK), classes),
        MessageHandler(filters.Regex(SKILL_LINK), skill),
        CommandHandler("report", _view(_report)),
        CommandHandler("professions", _view(_professions)),
        MessageHandler(filters.Regex(PROF_LINK), profession_guide),
        CommandHandler("settings", settings),
        CommandHandler("language", language),
        CommandHandler("help", help_cmd),
    ]
