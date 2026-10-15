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

from oathforge.ai import moderation
from oathforge.bot.handlers.common import current_view, edit_or_send, load, offer_keyboard, send
from oathforge.bot import render
from oathforge.bot.keyboards import btn, cb, grid, markup
from oathforge.bot.render import CLASS_ICONS, attribute
from oathforge.content import get_content
from oathforge.database.session import session_scope
from oathforge.engine import pointbuy
from oathforge.engine.checks import modifier
from oathforge.engine.progression import max_hp
from oathforge.i18n import t
from oathforge.services import audit, characters

NAME, GENDER, LINEAGE, BACKGROUND, CLASS, ABILITIES, CONFIRM, CUSTOM_TEXT, CUSTOM_SKILLS = range(9)
GENDERS = ("male", "female")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    async with session_scope() as session:
        user, char = await load(session, update)
        lang = user.language
        if char is not None:
            await offer_keyboard(update, user, lang, force=True)
            text, kb = await current_view(session, char, lang)
    if char is not None:
        await send(update, text, kb)
        return ConversationHandler.END
    context.user_data["lang"] = lang
    context.user_data["new"] = {}
    await send(update, t(lang, "create.welcome"), markup([[btn(t(lang, "btn.rulebook"), cb("rb", "index"))]]))
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
    await edit_or_send(update, *background_step(lang))
    return BACKGROUND


def background_step(lang: str, everything: bool = False):
    """The basic backgrounds explained, as buttons; "More…" swaps in a button for every background."""
    c = get_content()
    lines = [t(lang, "create.ask_background"), ""]
    listed = {k: bg for k, bg in c.backgrounds.items() if not bg.custom}
    if everything:
        rows = grid([btn(f"{bg.icon} {bg.name.get(lang)}", cb("cc", f"bg:{k}")) for k, bg in listed.items()])
        rows.append([btn(t(lang, "create.bg_basics"), cb("cc", "bgl:basic"))])
        lines.append(t(lang, "create.bg_all"))
    else:
        basic = {k: bg for k, bg in listed.items() if bg.basic}
        rows = [[btn(f"{bg.icon} {bg.name.get(lang)}", cb("cc", f"bg:{k}"))] for k, bg in basic.items()]
        rows.append([btn(t(lang, "create.bg_more", n=len(listed)), cb("cc", "bgl:all"))])
        lines += [f"{bg.icon} <b>{escape(bg.name.get(lang))}</b>: {escape(bg.description.get(lang))}\n"
                  f"<i>{render.background_line(bg, lang)}</i>\n" for bg in basic.values()]
    if any(bg.custom for bg in c.backgrounds.values()):
        rows.append([btn(t(lang, "create.custom_btn"), cb("cc", "bgc"))])
    return "\n".join(lines), markup(rows)


async def more_backgrounds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    everything = q.data.split("|")[1] == "bgl:all"  # "cc|bgl:all|-"
    await edit_or_send(update, *background_step(lang, everything=everything))
    return BACKGROUND


async def got_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    key = q.data.split("|")[1].split(":")[1]
    c = get_content()
    new = context.user_data.get("new", {})
    if key not in c.backgrounds or c.backgrounds[key].custom or "lineage" not in new:
        return BACKGROUND
    new["background"] = key
    new.pop("custom", None)
    await edit_or_send(update, *class_step(lang))
    return CLASS


def class_step(lang: str):
    c = get_content()
    lines = [t(lang, "create.ask_class"), ""]
    lines += [f"{CLASS_ICONS.get(k, '•')} <b>{cl.name.get(lang)}</b> · 🎲 d{cl.hit_die}: {cl.description.get(lang)}"
              for k, cl in c.classes.items()]
    rows = [[btn(f"{CLASS_ICONS.get(k, '•')} {cl.name.get(lang)}", cb("cc", f"cls:{k}"))] for k, cl in c.classes.items()]
    return "\n".join(lines), markup(rows)


# ---------------------------------------------------------------- a background of your own

async def ask_custom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "es")
    if "lineage" not in context.user_data.get("new", {}):
        return BACKGROUND
    kb = markup([[btn(t(lang, "create.custom_back"), cb("cc", "bgl:basic"))]])
    await edit_or_send(update, t(lang, "create.custom_ask", title_max=moderation.TITLE_MAX,
                                 story_max=moderation.STORY_MAX), kb)
    return CUSTOM_TEXT


async def got_custom_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """The AI reviews the name and story; without an answer from it, no custom background (pick a listed one)."""
    lang = context.user_data.get("lang", "es")
    new = context.user_data.get("new", {})
    back = markup([[btn(t(lang, "create.custom_back"), cb("cc", "bgl:basic"))]])
    parts = moderation.split_background(update.message.text or "")
    if parts is None:
        await send(update, t(lang, "create.custom_bad", title_max=moderation.TITLE_MAX,
                             story_min=moderation.STORY_MIN, story_max=moderation.STORY_MAX), back)
        return CUSTOM_TEXT
    title, story = parts
    await send(update, t(lang, "create.custom_checking"))
    async with session_scope() as session:
        user, _ = await load(session, update)
        user_id = user.id
    review = await moderation.review_background(context.bot_data["llm"], lang=lang, title=title, story=story,
                                                user_id=user_id)
    if review is None:
        await send(update, t(lang, "create.custom_unavailable"), back)
        return CUSTOM_TEXT
    if not review.ok:
        await send(update, t(lang, "create.custom_rejected", reason=escape(review.reason or "…")), back)
        return CUSTOM_TEXT
    new["custom"] = {"title": review.title, "story": story, "skills": []}
    await send(update, *custom_skills_panel(new, lang))
    return CUSTOM_SKILLS


def custom_skills_panel(new: dict, lang: str):
    c = get_content()
    custom = new["custom"]
    chosen = custom["skills"]
    lines = [t(lang, "create.custom_ok", title=escape(custom["title"])), f"<i>{escape(custom['story'])}</i>", "",
             t(lang, "create.custom_skills", n=characters.CUSTOM_SKILLS, chosen=len(chosen))]
    buttons = [btn(("✅ " if key in chosen else f"{c.abilities[s.ability].icon} ") + s.name.get(lang),
                   cb("cc", f"sk:{key}")) for key, s in c.skills.items()]
    rows = grid(buttons)
    if len(chosen) == characters.CUSTOM_SKILLS:
        rows.append([btn(t(lang, "btn.continue"), cb("cc", "sk:ok"))])
    rows.append([btn(t(lang, "create.custom_back"), cb("cc", "bgl:basic"))])
    return "\n".join(lines), markup(rows)


async def got_custom_skill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tap a skill to take or drop it; Continue once the 2 are chosen."""
    q = update.callback_query
    lang = context.user_data.get("lang", "es")
    new = context.user_data.get("new", {})
    key = q.data.split("|")[1].split(":")[1]
    if "custom" not in new:
        await q.answer()
        return BACKGROUND
    chosen = new["custom"]["skills"]
    if key == "ok":
        if len(chosen) != characters.CUSTOM_SKILLS:
            await q.answer(t(lang, "create.custom_skills_left", n=characters.CUSTOM_SKILLS), show_alert=True)
            return CUSTOM_SKILLS
        await q.answer()
        new["background"] = next(k for k, bg in get_content().backgrounds.items() if bg.custom)
        await edit_or_send(update, *class_step(lang))
        return CLASS
    if key not in get_content().skills:
        await q.answer()
        return CUSTOM_SKILLS
    if key in chosen:
        chosen.remove(key)
    elif len(chosen) < characters.CUSTOM_SKILLS:
        chosen.append(key)
    else:
        await q.answer(t(lang, "create.custom_skills_full", n=characters.CUSTOM_SKILLS), show_alert=True)
        return CUSTOM_SKILLS
    await q.answer()
    await edit_or_send(update, *custom_skills_panel(new, lang))
    return CUSTOM_SKILLS


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
    bg_name = escape(new["custom"]["title"]) if bg.custom else bg.name.get(lang)
    text = t(lang, "create.summary", name=escape(new["name"]),
             gender=t(lang, f"create.gender_btn.{new['gender']}"),
             lineage=f"{lin.icon} {lin.name.get(lang)}".strip(), background=f"{bg.icon} {bg_name}".strip(),
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
                                                     scores=new.get("scores"), custom=new.get("custom"))
            await audit.log(session, user_id=user.id, character_id=char.id, verb="create", payload=new)
        text, kb = await current_view(session, char, lang)
        await edit_or_send(update, t(lang, "create.done", name=escape(new["name"])))
        await offer_keyboard(update, user, lang, force=True)
    context.user_data.pop("new", None)
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
            BACKGROUND: [CallbackQueryHandler(got_background, pattern=r"^cc\|bg:"),
                         CallbackQueryHandler(more_backgrounds, pattern=r"^cc\|bgl:"),
                         CallbackQueryHandler(ask_custom, pattern=r"^cc\|bgc")],
            CUSTOM_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_custom_text),
                          CallbackQueryHandler(more_backgrounds, pattern=r"^cc\|bgl:")],
            CUSTOM_SKILLS: [CallbackQueryHandler(got_custom_skill, pattern=r"^cc\|sk:"),
                            CallbackQueryHandler(more_backgrounds, pattern=r"^cc\|bgl:")],
            CLASS: [CallbackQueryHandler(got_class, pattern=r"^cc\|cls:")],
            ABILITIES: [CallbackQueryHandler(got_ability, pattern=r"^cc\|ab:")],
            CONFIRM: [CallbackQueryHandler(confirm, pattern=r"^cc\|(ok|redo)")],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )
