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
from oathforge.bot.render import CLASS_ICONS, attribute
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine import pointbuy
from oathforge.engine.checks import modifier
from oathforge.engine.progression import max_hp
from oathforge.i18n import t
from oathforge.services import audit, characters

NAME, GENDER, LINEAGE, BACKGROUND, CLASS, ABILITIES, CONFIRM = range(7)
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
    lines += [f"{lin.icon} <b>{lin.name.get(lang)}</b>: {lin.description.get(lang)} <i>{lin.trait_text.get(lang)}</i>"
              for lin in c.lineages.values()]
    rows = [[btn(f"{lin.icon} {lin.name.get(lang)}", cb("cc", f"lin:{k}"))] for k, lin in c.lineages.items()]
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
    lines += [f"{bg.icon} <b>{bg.name.get(lang)}</b>: {bg.description.get(lang)} "
              f"<i>({', '.join(c.skills[s].name.get(lang) for s in bg.skills)})</i>" for bg in c.backgrounds.values()]
    rows = [[btn(f"{bg.icon} {bg.name.get(lang)}", cb("cc", f"bg:{k}"))] for k, bg in c.backgrounds.items()]
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
    lines += [f"{CLASS_ICONS.get(k, '•')} <b>{cl.name.get(lang)}</b> · 🎲 d{cl.hit_die}: {cl.description.get(lang)}"
              for k, cl in c.classes.items()]
    rows = [[btn(f"{CLASS_ICONS.get(k, '•')} {cl.name.get(lang)}", cb("cc", f"cls:{k}"))] for k, cl in c.classes.items()]
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
    new["scores"] = pointbuy.base()
    text, kb = abilities_panel(new, lang)
    await edit_or_send(update, text, kb)
    return ABILITIES


def abilities_panel(new: dict, lang: str):
    """Point buy: every ability with lineage bonus, final modifier and what it is for."""
    c = get_content()
    cls = c.classes[new["class"]]
    lin = c.lineages[new["lineage"]]
    scores = new["scores"]
    final = characters.starting_scores(new["class"], new["lineage"], scores)
    lines = [t(lang, "create.ask_abilities", cls=cls.name.get(lang), left=pointbuy.left(scores),
               budget=pointbuy.BUDGET), ""]
    rows = []
    for a, info in c.abilities.items():
        bonus = lin.bonuses.get(a, 0)
        extra = t(lang, "create.lineage_bonus", bonus=f"{bonus:+d}") if bonus else ""
        star = " ★" if a == cls.primary else ""
        lines.append(f"<b>{attribute(a, final[a], lang)}</b>{star}{extra}")
        lines.append(f"<i>{escape(info.effect.get(lang))}</i>")
        rows.append([btn("➖", cb("cc", f"ab:{a}:-")),
                     btn(f"{info.icon} {info.short.get(lang)} {scores[a]}", cb("cc", f"ab:{a}:i")),
                     btn("➕", cb("cc", f"ab:{a}:+"))])
    hp = max_hp(cls.hit_die, modifier(final["con"]), 1)
    lines += ["", t(lang, "create.ability_hp", hp=hp)]
    rows.append([btn(t(lang, "btn.recommended", cls=cls.name.get(lang)), cb("cc", "ab:rec")),
                 btn(t(lang, "btn.reset_points"), cb("cc", "ab:reset"))])
    rows.append([btn(t(lang, "btn.continue"), cb("cc", "ab:ok"))])
    return "\n".join(lines), markup(rows)


async def got_ability(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    lang = context.user_data.get("lang", "es")
    c = get_content()
    new = context.user_data.get("new", {})
    if not {"name", "gender", "lineage", "background", "class", "scores"} <= set(new):
        await q.answer()
        return ABILITIES
    parts = q.data.split("|")[1].split(":")[1:]
    scores = new["scores"]
    if parts[0] == "ok":
        left = pointbuy.left(scores)
        if left > 0:
            await q.answer(t(lang, "create.points_left", left=left), show_alert=True)
            return ABILITIES
        await q.answer()
        return await _summary(update, new, lang)
    if parts[0] in pointbuy.ABILITIES and len(parts) == 2 and parts[1] == "i":
        info = c.abilities[parts[0]]
        await q.answer(f"{info.name.get(lang)}: {info.effect.get(lang)}"[:200], show_alert=True)
        return ABILITIES
    if parts[0] == "rec":
        new["scores"] = dict(c.classes[new["class"]].array)
    elif parts[0] == "reset":
        new["scores"] = pointbuy.base()
    elif parts[0] in pointbuy.ABILITIES and len(parts) == 2:
        before = scores
        new["scores"] = pointbuy.change(scores, parts[0], 1 if parts[1] == "+" else -1)
        if new["scores"] == before:
            await q.answer(t(lang, "create.cannot_change"), show_alert=False)
            return ABILITIES
    await q.answer()
    text, kb = abilities_panel(new, lang)
    await edit_or_send(update, text, kb)
    return ABILITIES


async def _summary(update: Update, new: dict, lang: str) -> int:
    c = get_content()
    cls = c.classes[new["class"]]
    scores = characters.starting_scores(new["class"], new["lineage"], new["scores"])
    stats = [attribute(a, scores[a], lang) for a in c.abilities]
    stats = "\n".join(" · ".join(stats[i:i + 3]) for i in range(0, len(stats), 3))
    hp = max_hp(cls.hit_die, modifier(scores["con"]), 1)
    lin, bg = c.lineages[new["lineage"]], c.backgrounds[new["background"]]
    text = t(lang, "create.summary", name=escape(new["name"]),
             gender=t(lang, f"create.gender_btn.{new['gender']}"),
             lineage=f"{lin.icon} {lin.name.get(lang)}".strip(), background=f"{bg.icon} {bg.name.get(lang)}".strip(),
             cls=f"{CLASS_ICONS.get(new['class'], '')} {cls.name.get(lang)}".strip(), stats=stats, hp=hp)
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
    if not {"name", "gender", "lineage", "background", "class", "scores"} <= set(new):
        await edit_or_send(update, t(lang, "create.ask_name"))
        return NAME
    async with session_scope() as session:
        user, char = await load(session, update, lock=True)
        if char is None:
            char = await characters.create_character(session, user, new["name"], new["lineage"],
                                                     new["background"], new["class"], new["gender"],
                                                     scores=new.get("scores"))
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
            ABILITIES: [CallbackQueryHandler(got_ability, pattern=r"^cc\|ab:")],
            CONFIRM: [CallbackQueryHandler(confirm, pattern=r"^cc\|(ok|redo)")],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )
