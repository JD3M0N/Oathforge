"""/start and the character creation wizard."""

import warnings
from html import escape

from telegram import Update
from telegram.warnings import PTBUserWarning
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from oathforge.bot.handlers.common import current_view, edit_or_send, load, send
from oathforge.bot.keyboards import btn, cb, markup
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine.checks import modifier
from oathforge.engine.progression import max_hp
from oathforge.i18n import t
from oathforge.services import audit, characters

NAME, GENDER, LINEAGE, BACKGROUND, CLASS, CONFIRM = range(6)
GENDERS = ("male", "female")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = user.language
        if char is not None:
            text, kb = await current_view(session, char, lang)
    if char is not None:
        await send(update, text, kb)
        return ConversationHandler.END
    context.user_data["lang"] = lang
    context.user_data["new"] = {}
    await send(update, t(lang, "create.welcome"))
    await send(update, t(lang, "create.ask_name"))
    return NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "es")
    name = update.message.text.strip()
    if not characters.valid_name(name):
        await send(update, t(lang, "create.bad_name"))
        return NAME
    context.user_data["new"] = {"name": name}
    rows = [[btn(t(lang, f"create.gender_btn.{g}"), cb("cc", f"gen:{g}")) for g in GENDERS]]
    await send(update, t(lang, "create.ask_gender", name=escape(name)), markup(rows))
    return GENDER


async def got_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    key = q.data.split("|")[1].split(":")[1]
    new = context.user_data.get("new", {})
    if key not in GENDERS or "name" not in new:
        return GENDER
    new["gender"] = key
    c = get_content()
    lines = [t(lang, "create.ask_lineage", name=escape(new["name"])), ""]
    lines += [f"<b>{lin.name.get(lang)}</b>: {lin.description.get(lang)} <i>{lin.trait_text.get(lang)}</i>"
              for lin in c.lineages.values()]
    rows = [[btn(lin.name.get(lang), cb("cc", f"lin:{k}"))] for k, lin in c.lineages.items()]
    await edit_or_send(update, "\n".join(lines), markup(rows))
    return LINEAGE


async def got_lineage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    key = q.data.split("|")[1].split(":")[1]
    c = get_content()
    if key not in c.lineages or not {"name", "gender"} <= set(context.user_data.get("new", {})):
        return LINEAGE
    context.user_data["new"]["lineage"] = key
    lines = [t(lang, "create.ask_background"), ""]
    lines += [f"<b>{bg.name.get(lang)}</b>: {bg.description.get(lang)} "
              f"<i>({', '.join(c.skills[s].name.get(lang) for s in bg.skills)})</i>" for bg in c.backgrounds.values()]
    rows = [[btn(bg.name.get(lang), cb("cc", f"bg:{k}"))] for k, bg in c.backgrounds.items()]
    await edit_or_send(update, "\n".join(lines), markup(rows))
    return BACKGROUND


async def got_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    key = q.data.split("|")[1].split(":")[1]
    c = get_content()
    if key not in c.backgrounds:
        return BACKGROUND
    context.user_data["new"]["background"] = key
    lines = [t(lang, "create.ask_class"), ""]
    lines += [f"<b>{cl.name.get(lang)}</b>: {cl.description.get(lang)}" for cl in c.classes.values()]
    rows = [[btn(cl.name.get(lang), cb("cc", f"cls:{k}"))] for k, cl in c.classes.items()]
    await edit_or_send(update, "\n".join(lines), markup(rows))
    return CLASS


async def got_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    key = q.data.split("|")[1].split(":")[1]
    c = get_content()
    new = context.user_data.get("new", {})
    if key not in c.classes or not {"name", "gender", "lineage", "background"} <= set(new):
        return CLASS
    new["class"] = key
    cls = c.classes[key]
    scores = characters.starting_scores(key, new["lineage"])
    stats = " · ".join(f"{c.abilities[a].short.get(lang)} {scores[a]} ({modifier(scores[a]):+d})" for a in c.abilities)
    hp = max_hp(cls.hit_die, modifier(scores["con"]), 1)
    text = t(lang, "create.summary", name=escape(new["name"]), gender=t(lang, f"gender.{new['gender']}"),
             lineage=c.lineages[new["lineage"]].name.get(lang),
             background=c.backgrounds[new["background"]].name.get(lang), cls=cls.name.get(lang),
             stats=stats, hp=hp)
    rows = [[btn(t(lang, "btn.confirm"), cb("cc", "ok")), btn(t(lang, "btn.restart"), cb("cc", "redo"))]]
    await edit_or_send(update, text, markup(rows))
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    if q.data.startswith("cc|redo"):
        context.user_data["new"] = {}
        await edit_or_send(update, t(lang, "create.ask_name"))
        return NAME
    new = context.user_data.get("new", {})
    if not {"name", "gender", "lineage", "background", "class"} <= set(new):
        await edit_or_send(update, t(lang, "create.ask_name"))
        return NAME
    async with session_scope() as session:
        user, char = await load(session, update, lock=True)
        if char is None:
            char = await characters.create_character(session, user, new["name"], new["lineage"],
                                                     new["background"], new["class"], new["gender"])
            await audit.log(session, user_id=user.id, character_id=char.id, verb="create", payload=new)
        text, kb = await current_view(session, char, lang)
    context.user_data.pop("new", None)
    await edit_or_send(update, t(lang, "create.done", name=escape(new["name"])))
    await send(update, text, kb)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "es")
    context.user_data.pop("new", None)
    await send(update, t(lang, "create.cancelled"))
    return ConversationHandler.END


def handler() -> ConversationHandler:
    # Creation is tracked per user, not per message; PTB warns about that combination by default.
    warnings.filterwarnings("ignore", message=".*per_message=False.*", category=PTBUserWarning)
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            GENDER: [CallbackQueryHandler(got_gender, pattern=r"^cc\|gen:")],
            LINEAGE: [CallbackQueryHandler(got_lineage, pattern=r"^cc\|lin:")],
            BACKGROUND: [CallbackQueryHandler(got_background, pattern=r"^cc\|bg:")],
            CLASS: [CallbackQueryHandler(got_class, pattern=r"^cc\|cls:")],
            CONFIRM: [CallbackQueryHandler(confirm, pattern=r"^cc\|(ok|redo)")],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )
