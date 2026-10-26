"""Journal, missions, chronicle, stats and achievements."""

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.bot import achievement_views
from oathforge.bot.keyboards import btn, cb, markup, nonce
from oathforge.bot.render.common import ACTIVITY_ICON, MAX_MESSAGE, RULE, _go_button, journal_tabs
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.i18n import t
from oathforge.services import achievements, activities, characters, chronicle_log, exploration, quests, world_map

QUEST_ICONS = {"locked": "🔒", "available": "❔", "active": "📜", "ready": "✅", "completed": "✅", "failed": "❌"}


def _objective_line(obj, done: int, lang: str) -> str:
    target = quests.objective_target(obj)[lang]
    mark = "☑️" if done >= obj.count else "▫️"
    count = f" {done}/{obj.count}" if obj.count > 1 else ""
    return f"{mark} {escape(t(lang, quests.objective_key(obj), target=target))}{count}"


async def journal(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The journal's cover: what you are doing, what comes next, and the tap that takes you there."""
    c = get_content()
    n = nonce()
    ach = await achievements.snapshot(session, char)
    lines = [t(lang, "journal.title"), RULE]
    rows: list[list] = []
    act = await activities.open_activity(session, char)
    if act is not None:
        lines.append(
            f"{ACTIVITY_ICON.get(act.skill, '⏳')} "
            + t(
                lang,
                "journal.now_activity",
                what=escape(activities.describe(act, lang)),
                minutes=activities.remaining_minutes(act),
            )
        )
        rows.append([btn(t(lang, "btn.see_activity"), cb("acts"))])
    trip_to = exploration.trip(char) if char.state == "idle" else None
    if trip_to:  # an ambush stopped the trip halfway: carry on from here too
        lines.append(t(lang, "journal.now_trip", place=escape(c.locations[trip_to].phrase()[lang])))
        rows.append(
            [btn(t(lang, "btn.continue_trip", place=c.locations[trip_to].phrase()[lang]), cb("go", trip_to, n))]
        )
    current = [
        (k, q, p)
        for k, q, p in await quests.journal(session, char)
        if quests.stage_of(q, p)[1] in ("active", "available", "ready")
    ]
    if current:
        lines.append("")
        lines.append(f"<b>{t(lang, 'journal.current')}</b>")
        for key, quest, prog in current:
            stage, state = quests.stage_of(quest, prog)
            lines.append(f"{QUEST_ICONS[state]} <b>{escape(quest.name.get(lang))}</b>")
            lines.append(f"<i>{escape(quest.stages[stage].journal.get(lang))}</i>")
            lines += [_objective_line(o, done, lang) for o, done in quests.objective_progress(quest, prog)]
            if state == "ready" and quest.giver:  # it is done; somebody is owed the news
                lines.append(
                    t(
                        lang,
                        "quest.ready",
                        quest=escape(quest.name.get(lang)),
                        npc=escape(c.npcs[quest.giver].name.get(lang)),
                    )
                )
            rows.append([btn(f"{QUEST_ICONS[state]} {quest.name.get(lang)}", cb("jq", key))])
    else:
        lines += ["", f"<i>{t(lang, 'journal.no_current')}</i>"]
    # Never a dead end: the objective of a mission, or whoever hands them out, is always one tap away.
    goals = await exploration.objective_routes(session, char)
    if goals:
        lines += ["", t(lang, "map.objective")]
        for quest, route in goals:
            lines.append(
                t(
                    lang,
                    "map.objective_line",
                    quest=escape(quest.get(lang, quest.get("en"))),
                    place=escape(c.locations[route.to].name.get(lang)),
                )
            )
            rows.append(_go_button(route, lang, n, "📜"))
    elif not current:
        rows += _giver_buttons(char, lang, n)
    lines += achievement_views.tracked(ach, lang)
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows + journal_tabs("jr", lang))


def _giver_buttons(char: Character, lang: str, n: str) -> list[list]:
    """With nothing in progress, point at the quest giver instead of saying there is nothing to do."""
    c = get_content()
    for quest in sorted(c.quests.values(), key=lambda q: q.order):
        npc = c.npcs.get(quest.giver) if quest.giver else None
        place = (npc.schedule or {}).get("day") if npc else None
        if place and place != char.location:
            route = world_map.route_to(char, place)
            if route:
                return [_go_button(route, lang, n, "🗣️")]
    return []


FINISHED = ("completed", "failed")


async def missions(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """/quests: what is in progress or on offer, and below it everything already finished."""
    entries = await quests.journal(session, char)
    done = sum(1 for _, q, p in entries if quests.stage_of(q, p)[1] == "completed")
    lines = [t(lang, "journal.missions_title", done=done, total=len(entries)), ""]
    rows = []
    for key, quest, prog in entries:
        _, state = quests.stage_of(quest, prog)
        if state in ("active", "available", "ready"):
            rows.append([btn(f"{QUEST_ICONS[state]} {quest.name.get(lang)}", cb("jq", key))])
    lines.append(f"<i>{t(lang, 'journal.missions_hint' if rows else 'journal.no_current')}</i>")
    finished = [(k, q, p) for k, q, p in entries if quests.stage_of(q, p)[1] in FINISHED]
    if finished:
        lines += ["", f"<b>{t(lang, 'journal.log_title', n=len(finished))}</b>"]
        rows += [
            [btn(f"{QUEST_ICONS[quests.stage_of(q, p)[1]]} {q.name.get(lang)}", cb("jq", k))] for k, q, p in finished
        ]
    return "\n".join(lines), markup(rows + journal_tabs("jrm", lang))


def fmt_int(n: int, lang: str) -> str:
    """3.400 in Spanish, 3,400 in English."""
    return f"{n:,}".replace(",", "." if lang == "es" else ",")


async def stats_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The journal's statistics: how far you walked, where you have been, what you fought and what you made."""
    c = get_content()
    st = characters.stats(char)
    places = [p for p in st.get("places", []) if p in c.locations]
    cities = {c.locations[p].zone for p in places if c.zones[c.locations[p].zone].kind == "city"}
    kills = {k: v.get("killed", 0) for k, v in (char.bestiary or {}).items() if v.get("killed")}
    top = sorted(kills.items(), key=lambda kv: -kv[1])[:3]
    lines = [
        t(lang, "stats.title"),
        RULE,
        t(lang, "stats.distance", yards=fmt_int(int(st.get("yards", 0)), lang)),
        t(lang, "stats.places", places=len(places), cities=len(cities)),
        t(
            lang,
            "stats.battles",
            won=st.get("battles_victory", 0),
            lost=st.get("battles_defeat", 0),
            fled=st.get("battles_fled", 0),
        ),
        t(lang, "stats.kills", n=sum(kills.values())),
    ]
    if top:
        lines.append(
            "      " + escape(", ".join(f"{c.monsters[k].name.get(lang)} ×{n}" for k, n in top if k in c.monsters))
        )
    lines += [
        t(lang, "stats.dodges", n=st.get("dodges", 0)),
        t(lang, "stats.crits", n=st.get("crits", 0)),
        t(lang, "stats.activities", n=st.get("activities", 0)),
        "",
        f"<i>{t(lang, 'stats.since')}</i>",
    ]
    # Counted from the chronicle: every one of these is a fact the engine recorded.
    counted = await chronicle_log.counts(session, char)
    ach = await achievements.snapshot(session, char)
    lines += [
        "",
        t(lang, "stats.chronicle_title"),
        RULE,
        t(lang, "stats.quests", n=counted["quests"]),
        t(lang, "stats.crafts", n=counted["crafts"], recipes=counted["recipes"]),
        t(lang, "stats.discoveries", n=counted["discoveries"]),
        t(lang, "stats.monsters_known", n=counted["monsters_known"], killed=counted["species_killed"]),
        t(lang, "stats.levels", n=counted["levels"]),
        t(lang, "stats.achievements", n=ach["count"], points=ach["points"]),
        "",
        f"<i>{t(lang, 'stats.since_chronicle')}</i>",
    ]
    return "\n".join(lines)[:MAX_MESSAGE], markup(journal_tabs("jrs", lang))


def _fact_line(fact, lang: str) -> str | None:
    """One chronicle entry, named from the content. An unknown id leaves the entry out."""
    c = get_content()
    data = fact.data or {}

    def named(pool, key):
        entry = pool.get(data.get(key))
        return escape(entry.name.get(lang)) if entry is not None else None

    if fact.kind in ("seen", "kill", "secrets"):
        what = named(c.monsters, "monster")
    elif fact.kind in ("quest", "quest_start"):
        what = named(c.quests, "quest")
    elif fact.kind == "visit":
        what = named(c.locations, "location")
    elif fact.kind == "unlock":
        what = named(c.achievements, "key")
    elif fact.kind == "craft":
        recipe = c.recipes.get(data.get("recipe"))
        what = escape(c.items[next(iter(recipe.outputs))].name.get(lang)) if recipe else None
    elif fact.kind == "discovery":
        place = (data.get("key") or "").split(":")[0]  # the discovery id is "<place>:<secret>"
        what = escape(c.locations[place].name.get(lang)) if place in c.locations else None
    elif fact.kind == "level":
        what = str(data.get("level", ""))
    elif fact.kind == "profession":
        what = named(c.professions, "key")
    elif fact.kind == "mastery":
        what = escape(characters.mastery_name(data["skill"])[lang]) if data.get("skill") else None
    elif fact.kind == "decision":
        what = t(lang, f"book.decision_text.{data.get('key')}")
    elif fact.kind == "combat":
        if data.get("location") not in c.locations:
            return t(lang, "book.combat_nowhere")
        what = escape(c.locations[data["location"]].name.get(lang))
    else:
        return None
    if what is None:
        return None
    return t(lang, f"book.{fact.kind}", what=what, rank=data.get("rank", 0))


async def chronicle(
    session: AsyncSession, char: Character, lang: str, page: str = "0"
) -> tuple[str, InlineKeyboardMarkup]:
    """The journal's chronicle: the facts the engine recorded, newest first. No AI: every line is an event."""
    number = int(page) if str(page).lstrip("-").isdigit() else 0
    facts, more, first_day = await chronicle_log.page(session, char, number)
    title = achievement_views.title_of(await achievements.snapshot(session, char), lang)
    lines = [t(lang, "book.title"), RULE]
    if title:
        lines.insert(1, t(lang, "book.by", name=escape(char.name), title=escape(title)))
    day = None
    old = False
    for fact in facts:
        if fact.retroactive and not old:
            lines.append(f"<i>{t(lang, 'book.before')}</i>")
            old, day = True, None
        text = _fact_line(fact, lang)
        if text is None:
            continue
        if not fact.retroactive and fact.game_day != day:
            day = fact.game_day
            lines.append(f"<b>{t(lang, 'book.day', day=day - first_day + 1)}</b>")
        lines.append(text)
    if not facts:
        lines.append(f"<i>{t(lang, 'book.empty')}</i>")
    rows = []
    nav = ([btn("◀", cb("jrc", str(number - 1)))] if number else []) + (
        [btn("▶", cb("jrc", str(number + 1)))] if more else []
    )
    if nav:
        rows.append(nav)
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows + journal_tabs("jrc", lang))


async def mission(session: AsyncSession, char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    back = markup([[btn(t(lang, "btn.back"), cb("jrm"))]])
    entry = next(((q, p) for k, q, p in await quests.journal(session, char) if k == key), None)
    if entry is None:
        return t(lang, "quest.err.unavailable"), back
    quest, prog = entry
    stage, state = quests.stage_of(quest, prog)
    if state == "locked":
        lines = [
            f"🔒 <b>{t(lang, 'journal.locked_name')}</b>",
            "",
            f"<i>{escape(quest.stages[stage].journal.get(lang))}</i>",
        ]
        if quest.after:
            lines += ["", t(lang, "journal.unlocks_after", quest=escape(c.quests[quest.after].name.get(lang)))]
        return "\n".join(lines), back
    lines = [f"{QUEST_ICONS[state]} <b>{escape(quest.name.get(lang))}</b>"]
    if quest.giver:
        npc = c.npcs[quest.giver]
        lines.append(t(lang, "journal.giver", npc=escape(npc.name.get(lang)), title=escape(npc.title.get(lang))))
    lines += ["", escape(quest.summary.get(lang)), "", f"<i>{escape(quest.stages[stage].journal.get(lang))}</i>"]
    objectives = quests.objective_progress(quest, prog)
    if objectives:
        lines += ["", f"<b>{t(lang, 'journal.objectives')}</b>", *(_objective_line(o, n, lang) for o, n in objectives)]
    if quest.hint and state not in ("completed", "failed"):
        lines += ["", f"🧭 {escape(quest.hint.get(lang))}"]
    rewards = _rewards_line(quest.rewards, lang)
    if rewards:
        lines += ["", f"<b>{t(lang, 'journal.rewards')}</b> {rewards}"]
    return "\n".join(lines)[:MAX_MESSAGE], back


def _rewards_line(effects: list[dict], lang: str) -> str:
    c = get_content()
    parts = []
    for eff in effects:
        ((kind, arg),) = eff.items()
        if kind == "xp":
            parts.append(f"✨ {arg} XP")
        elif kind == "gold":
            parts.append(f"🪙 {arg}")
        elif kind == "give_item":
            parts += [f"🎁 {c.items[i].name.get(lang)}" + (f" ×{q}" if q > 1 else "") for i, q in arg.items()]
    return " · ".join(escape(p) for p in parts)


async def achievements_view(session, char, lang, arg="-"):
    return achievement_views.view(await achievements.snapshot(session, char), lang, arg)
