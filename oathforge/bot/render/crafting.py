"""Field activities, masteries, hobbies, professions, recipes, tools and specializations."""

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine import gathering, timings
from oathforge.i18n import t
from oathforge.services import (
    activities,
    characters,
    crafting,
    exploration,
    inventory,
    professions,
    quests,
    specializations,
)
from oathforge.services.events import Outcome, render_event
from oathforge.bot.render.common import (
    ACTIVITY_ICON,
    LEVEL_KEYS,
    MASTERY_ICON,
    MAX_MESSAGE,
    REPORT_ICON,
    RULE,
    RULE_NUMBER,
    SKINNING_TOOL,
    creature_icon,
    discipline_icon,
    discipline_label,
    item_stats,
    panel_only,
    rule_numbers,
)


END_RESULT = {"won": "victory", "fled": "fled", "lost": "defeat"}


def activity_title(act, lang: str) -> str | None:
    """ "Rastreo en Prado de los Colmillos · 🏆 Victoria" for an activity that ended in a fight."""
    outcome = (act.result or {}).get("outcome", "")
    result = END_RESULT.get(outcome.rpartition("_")[2])
    if result is None:
        return None
    return f"{activities.describe(act, lang)} · {REPORT_ICON.get(result, '')} {t(lang, 'report.result.' + result)}"


def activity_result(
    outcome: Outcome,
    skill: str,
    lang: str,
    chronicle: str | None = None,
    footer: str | None = None,
    title: str | None = None,
) -> str:
    """A finished field activity in one message: "✅ Terminas tu trabajo en X" with the craft's emoji, the
    chronicle, what was obtained and the XP, and "Crónica 1/15"."""
    head, rest = None, []
    for ev in outcome.events:
        if ev.key in LEVEL_KEYS or panel_only(ev.key):
            continue
        if head is None and (ev.key.startswith("activity.done.") or ev.key == "activity.track_tracks"):
            head = escape(render_event(ev, lang))
        else:
            rest.append(f"• {escape(render_event(ev, lang))}")
    head = head or (escape(title) if title else None)
    parts = [f"{ACTIVITY_ICON.get(skill, '✅')} <b>{head}</b>" if head else ""]
    if chronicle:
        parts.append(f"📜 <i>{escape(chronicle)}</i>")
    parts.append("\n".join(rest))
    if footer:
        parts.append(f"<i>{escape(footer)}</i>")
    return "\n\n".join(p for p in parts if p)[:MAX_MESSAGE]


def activity_panel(
    char: Character, act, lines: list[str], n: str, lang: str, started: str | None = None
) -> tuple[str, InlineKeyboardMarkup]:
    """The scene while a field activity runs: what, how long is left, Refresh / Abandon. It ends by itself
    (the bot sends the result), so there is nothing to collect. ``started``: the line of the moment it began."""
    seconds = activities.remaining_seconds(act)
    rest = act.kind in activities.REST_KINDS
    if seconds == 0:
        left = t(lang, "activity.ready_rest" if rest else "activity.ready")
    elif seconds < 60:
        left = t(lang, "activity.left_seconds", seconds=seconds)
    else:
        left = t(lang, "activity.left", minutes=activities.remaining_minutes(act))
    icon = ACTIVITY_ICON.get(act.skill, "⏳")
    head = escape(started) if started else t(lang, "activity.panel_title", what=escape(activities.describe(act, lang)))
    lines = lines[:2] + ["", f"{icon} {head}", f"⏳ {left}"]
    if act.kind == "stay":
        lines.append(t(lang, "activity.stay_warning"))
    lines += ["", f"<i>{t(lang, 'activity.busy_hint_rest' if rest else 'activity.busy_hint')}</i>"]
    rows = [[btn(t(lang, "btn.refresh"), cb("actc", "-", n)), btn(t(lang, "btn.abandon"), cb("actx", "-", n))]]
    return "\n".join(lines), markup(rows)


def seller_of(item_key: str) -> tuple[str, str] | None:
    """(npc, location) of whoever sells an item by day: where to buy the pickaxe you lack."""
    for key, npc in get_content().npcs.items():
        if npc.shop and item_key in npc.shop.items and npc.schedule.get("day"):
            return key, npc.schedule["day"]
    return None


async def activity_entries(session: AsyncSession, char: Character, lang: str, n: str = "-") -> list[tuple[str, object]]:
    """⚒ Activities: (line, button) for everything the hands can do here. The button is None when there is
    nothing to press (no gold for the inn); a missing tool offers the way to the shop that sells it."""
    c = get_content()
    loc = c.locations[char.location]
    night = exploration.is_night()
    out = []
    if loc.hunting:
        label = t(lang, "btn.hunt_night" if night and loc.night_encounters else "btn.hunt")
        out.append((f"<b>{label}</b> · <i>{t(lang, 'acts.desc.hunt')}</i>", btn(label, cb("hunt", "-", n))))
    labels = {
        "gather": "btn.gather_{}",
        "stay": "btn.stay",
        "track": "btn.track",
        "skin": "btn.skin",
        "rest": "btn.rest" if activities.rest_cost(char) else "btn.rest_free",
        "short_rest": "btn.short_rest",
    }
    for kind, skill, refusal in await activities.availability(session, char):
        seconds = activities.skin_seconds(characters.pending_skin(char)) if kind == "skin" else timings.SECONDS[kind]
        label = t(
            lang,
            labels[kind].format(skill),
            minutes=seconds // 60,
            seconds=seconds,
            cost=activities.rest_cost(char) or 0,
        )
        desc = t(lang, f"acts.desc.{kind}", minutes=seconds // 60, left=activities.short_rests_left(char))
        line = f"<b>{escape(label)}</b> · <i>{desc}</i>"
        tool = activities.tool_for(char, kind, skill)
        button = btn(label, cb("rest", "-", n) if kind == "rest" else cb("act", f"{kind}:{skill}", n))
        if refusal is None:
            if tool:
                line += f"\n      🧰 {escape(c.items[tool].name.get(lang))} ✅"
        elif refusal.error == "activity.err.no_tool":
            name = c.items[tool].name.get(lang)
            line += "\n      " + t(lang, "acts.missing", tool=escape(name))
            seller = seller_of(tool)
            button = None
            if seller and seller[1] == char.location:
                button = btn(t(lang, "btn.buy_tool", tool=name), cb("shop", seller[0]))
            elif seller:
                button = btn(
                    t(lang, "btn.buy_tool_at", tool=name, place=c.locations[seller[1]].phrase()[lang]),
                    cb("go", seller[1], n),
                )
        else:
            line += "\n      ❌ " + escape(render_event(refusal.events[0], lang))
            button = None
        out.append((line, button))
    if loc.stations:
        out.append(
            (
                f"<b>{t(lang, 'btn.craft')}</b> · <i>{t(lang, 'acts.desc.craft')}</i>",
                btn(t(lang, "btn.craft"), cb("crf")),
            )
        )
    if loc.healer is not None:
        label = t(lang, "btn.heal", cost=exploration.healer_price(char))
        out.append((f"<b>{label}</b> · <i>{t(lang, 'acts.desc.heal')}</i>", btn(label, cb("heal", "-", n))))
    return out


FIELD_MASTERIES = gathering.MASTERIES


def mastery_lines(char: Character, lang: str, skills: tuple[str, ...] = FIELD_MASTERIES) -> list[str]:
    """⛏️ Minería ★★ · 260/500 XP"""
    out = []
    for skill in skills:
        xp = characters.mastery_xp(char, skill)
        out.append(
            f"{MASTERY_ICON[skill]} {escape(t(lang, f'mastery.name.{skill}'))} "
            f"{_stars(gathering.rank_for(xp))} · {_progress(xp)}"
        )
    return out


def hobby_lines(char: Character, lang: str) -> list[str]:
    """Cooking and fishing: optional, no slot."""
    c = get_content()
    return [
        t(
            lang,
            "prof.line",
            icon=c.professions[k].icon,
            name=escape(c.professions[k].name.get(lang)),
            stars=_stars(professions.rank(char, k)),
            progress=_progress(professions.xp(char, k)),
        )
        + f" · /prof_{k}"
        for k in professions.hobbies()
    ]


def _stars(rank: int) -> str:
    return "★" * rank + "☆" * (gathering.MAX_RANK - rank)


def _progress(xp: int) -> str:
    nxt = gathering.next_threshold(xp)
    return f"{xp}/{nxt} XP" if nxt else f"{xp} XP"


def professions_line(char: Character, lang: str) -> str:
    """🛠️ Oficios 1/2: Alquimia ★☆☆☆☆"""
    c = get_content()
    mine = professions.active(char)
    names = ", ".join(
        f"{c.professions[k].icon} {c.professions[k].name.get(lang)} {_stars(professions.rank(char, k))}" for k in mine
    ) or t(lang, "sheet.no_professions")
    return t(lang, "sheet.professions", used=len(mine), slots=professions.SLOTS, list=escape(names))


def professions_view(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """/professions: your two professions, the others you know, the hobbies and the field masteries.
    At the guild, buttons to learn or swap."""
    c = get_content()
    mine = professions.active(char)
    lines = [t(lang, "prof.title", used=len(mine), slots=professions.SLOTS), ""]
    if not mine:
        lines.append(t(lang, "prof.none", slots=professions.SLOTS))
    for key, prof in c.professions.items():
        xp = professions.xp(char, key)
        if not prof.hobby and (key in mine or xp):
            lines.append(
                t(
                    lang,
                    "prof.line",
                    icon=prof.icon,
                    name=escape(prof.name.get(lang)),
                    stars=_stars(professions.rank(char, key)),
                    progress=_progress(xp),
                )
                + ("" if key in mine else " " + t(lang, "prof.inactive"))
                + f" · /prof_{key}"
            )
    others = [
        f"{p.icon} /prof_{k}"
        for k, p in c.professions.items()
        if not p.hobby and k not in mine and not professions.xp(char, k)
    ]
    if others:
        lines += ["", t(lang, "prof.guides", list=" · ".join(others))]
    lines += ["", t(lang, "prof.hobbies"), *hobby_lines(char, lang)]
    lines += ["", t(lang, "prof.masteries"), *mastery_lines(char, lang), ""]
    rows = []
    here = c.locations[char.location].teaches
    if here is not None:
        lines.append(t(lang, "prof.guild_hint", cost=professions.SWAP_COST))
        n = nonce()
        full = len(mine) >= professions.SLOTS
        learnable = [
            btn(
                t(
                    lang,
                    "btn.swap_for" if full else "btn.learn",
                    prof=f"{p.icon} {p.name.get(lang)}",
                    cost=professions.SWAP_COST,
                ),
                cb("profsw", k) if full else cb("plearn", k, n),
            )
            for k, p in c.professions.items()
            if k == here and k not in mine and not p.hobby
        ]
        rows += grid(learnable)
    else:
        lines.append(t(lang, "prof.go_guild"))
    rows.append(crafts_tabs(lang, "prof"))
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def crafts_tabs(lang: str, here: str) -> list:
    """🛠️ Professions · ⛏️ Masteries · 🍲 Hobbies: the three pages link to each other."""
    tabs = (("prof", "btn.tab_professions"), ("mst", "btn.tab_masteries"), ("hob", "btn.tab_hobbies"))
    return [btn(t(lang, label), cb(verb)) for verb, label in tabs if verb != here]


def _mastery_tool_and_places(skill: str, lang: str) -> tuple[str | None, list[str]]:
    c = get_content()
    if skill == "skinning":
        return SKINNING_TOOL, [m.name.get(lang) for m in c.monsters.values() if m.harvest]
    if skill == "tracking":
        return None, [loc.name.get(lang) for loc in c.locations.values() if loc.hunting]
    found = [(g.tool, loc.name.get(lang)) for loc in c.locations.values() for g in loc.gathering if g.skill == skill]
    return (found[0][0] if found else None), [place for _, place in found]


def mastery_entry(skill: str, lang: str, char: Character | None) -> list[str]:
    c = get_content()
    tool, places = _mastery_tool_and_places(skill, lang)
    head = f"{MASTERY_ICON[skill]} <b>{escape(t(lang, f'mastery.name.{skill}'))}</b>"
    if char is not None:
        xp = characters.mastery_xp(char, skill)
        head += f" {_stars(gathering.rank_for(xp))} · {_progress(xp)}"
    lines = [head, f"<i>{escape(t(lang, f'mastery.desc.{skill}'))}</i>"]
    if tool:
        lines.append(t(lang, "mastery.tool", tool=escape(c.items[tool].name.get(lang)), link=f"/item_{tool}"))
    if places:
        key = "mastery.beasts" if skill == "skinning" else "mastery.places"
        lines.append(t(lang, key, list=escape(", ".join(dict.fromkeys(places)))))
    return lines


def masteries_view(char: Character | None, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """/masteries: the field masteries, free for everyone, 0-5 with use."""
    lines = [t(lang, "mastery.title"), f"<i>{t(lang, 'mastery.intro', cap=round(gathering.BONUS_CAP * 100))}</i>", RULE]
    for skill in FIELD_MASTERIES:
        lines += [*mastery_entry(skill, lang, char), ""]
    rows = [crafts_tabs(lang, "mst")] if char is not None else [[btn(t(lang, "btn.tab_hobbies"), cb("hob"))]]
    if char is not None:  # the branch of each mastery and the tool it works with
        rows.append([btn(t(lang, "btn.specializations"), cb("spec")), btn(t(lang, "btn.tools"), cb("tools"))])
    return "\n".join(lines).rstrip()[:MAX_MESSAGE], markup(rows)


def hobbies_view(char: Character | None, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """/hobbies: optional, no profession slot (cooking, fishing)."""
    c = get_content()
    lines = [t(lang, "hobby.title"), f"<i>{t(lang, 'hobby.intro')}</i>", RULE]
    for k in professions.hobbies():
        prof = c.professions[k]
        head = f"{prof.icon} <b>{escape(prof.name.get(lang))}</b>"
        if char is not None:
            head += f" {_stars(professions.rank(char, k))} · {_progress(professions.xp(char, k))}"
        lines += [
            head,
            f"<i>{escape(prof.description.get(lang))}</i>",
            *_where(prof, lang),
            t(lang, "hobby.guide", link=f"/prof_{k}"),
            "",
        ]
    rows = [crafts_tabs(lang, "hob")] if char is not None else [[btn(t(lang, "btn.tab_masteries"), cb("mst"))]]
    return "\n".join(lines).rstrip()[:MAX_MESSAGE], markup(rows)


def swap_menu(char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Which active profession to drop for ``key``; the next step asks to confirm."""
    c = get_content()
    if key not in c.professions:
        return professions_view(char, lang)
    rows = [
        [btn(t(lang, "btn.replace", prof=c.professions[old].name.get(lang)), cb("profcf", f"{key}:{old}"))]
        for old in professions.active(char)
    ]
    rows.append([btn(t(lang, "btn.back"), cb("prof"))])
    return t(
        lang, "prof.swap_title", prof=escape(c.professions[key].name.get(lang)), cost=professions.SWAP_COST
    ), markup(rows)


def swap_confirm(char: Character, arg: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Drop one profession for another: the cost and a Confirm button."""
    c = get_content()
    key, _, old = arg.partition(":")
    if key not in c.professions or old not in professions.active(char):
        return professions_view(char, lang)
    text = t(
        lang,
        "prof.swap_confirm",
        old=escape(c.professions[old].name.get(lang)),
        prof=escape(c.professions[key].name.get(lang)),
        cost=professions.SWAP_COST,
        gold=char.gold,
    )
    rows = [[btn(t(lang, "btn.confirm"), cb("plearn", arg, nonce())), btn(t(lang, "btn.back"), cb("profsw", key))]]
    return text, markup(rows)


def _where(prof, lang: str) -> list[str]:
    """Where a profession is worked: its station, or for fishing the tool and the places."""
    if prof.station is not None:
        return [_station_place(prof.station, lang)]
    c = get_content()
    tool, places = _mastery_tool_and_places(prof.practice, lang)
    lines = [t(lang, "mastery.tool", tool=escape(c.items[tool].name.get(lang)), link=f"/item_{tool}")] if tool else []
    if places:
        lines.append(t(lang, "mastery.places", list=escape(", ".join(dict.fromkeys(places)))))
    return lines


def _station_place(station: str, lang: str) -> str:
    c = get_content()
    places = [loc.name.get(lang) for loc in c.locations.values() if station in loc.stations]
    return t(lang, "prof.station", station=t(lang, f"station.{station}"), place=escape(", ".join(places)))


RENAMED_PROFESSIONS = {"artificing": "engineering"}  # old /prof_<key> links keep working


def profession_page(key: str, lang: str, char: Character | None = None) -> tuple[str, InlineKeyboardMarkup | None]:
    """/prof_<key>: a profession or hobby at a glance, like /class_<key>: what it does, where, from what,
    and every recipe by rank (yours marked when the player has a character)."""
    c = get_content()
    key = RENAMED_PROFESSIONS.get(key, key)
    prof = c.professions.get(key)
    if prof is None:
        return professions_view(char, lang) if char else (t(lang, "prof.err.unknown"), None)
    lines = [
        f"{prof.icon} <b>{escape(prof.name.get(lang))}</b>" + (f" · {t(lang, 'prof.hobby_tag')}" if prof.hobby else ""),
        f"<i>{escape(prof.description.get(lang))}</i>",
        RULE,
    ]
    if prof.guide:
        guide = RULE_NUMBER.sub(lambda m: str(rule_numbers(lang).get(m.group(1), m.group(0))), prof.guide.get(lang))
        lines += [escape(guide), ""]
    lines += _where(prof, lang)
    if char is not None and (prof.hobby or key in professions.active(char) or professions.xp(char, key)):
        lines.append(
            t(
                lang,
                "prof.your_rank",
                stars=_stars(professions.rank(char, key)),
                progress=_progress(professions.xp(char, key)),
            )
        )
    recipes = sorted((r for r in c.recipes.values() if r.profession == key), key=lambda r: r.min_rank)
    if recipes:
        lines += [RULE, f"<b>{t(lang, 'prof.recipes')}</b>"]
    for r in recipes:
        mark = ("✅ " if professions.rank(char, key) >= r.min_rank else "🔒 ") if char is not None else ""
        outs = ", ".join(f"{c.items[i].label(lang)} ×{q}" for i, q in r.outputs.items())
        ins = " + ".join(f"{q} {c.items[i].label(lang)}" for i, q in r.ingredients.items())
        lines.append(f"{mark}<b>{t(lang, 'prof.rank_n', rank=r.min_rank)}</b> · {escape(outs)}")
        lines.append(f"      ← {escape(ins)}")
    rows = [[btn(t(lang, "btn.professions"), cb("prof"))]] if char is not None else []
    return "\n".join(lines)[:MAX_MESSAGE], (markup(rows) if rows else None)


async def craft_menu(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Recipes of your professions at this station: what you have, what is missing, and a button when ready."""
    c = get_content()
    lines = [t(lang, "craft.title", place=escape(c.locations[char.location].name.get(lang))), ""]
    prog = await quests.progress(session, char)
    recipes = crafting.recipes_here(char, {k for k, p in prog.items() if p.state == "active"})
    n = nonce()
    ready = []
    if not recipes:
        lines.append(t(lang, "craft.none"))
        for k in professions.usable(char):
            prof = c.professions[k]
            if prof.station is not None:
                lines.append(f"{prof.icon} {escape(prof.name.get(lang))}: {_station_place(prof.station, lang)}")
    for key, r in recipes.items():
        locked = crafting.rank_in(char, r.profession) < r.min_rank
        lacking = await crafting.missing(session, char, r)
        mark = "🔒" if locked else "❌" if lacking else "✅"
        out_key, qty = next(iter(r.outputs.items()))
        rank = t(lang, "craft.locked", rank=r.min_rank) if locked else ""
        lines.append(
            t(
                lang,
                "craft.recipe",
                mark=mark,
                item=escape(c.items[out_key].label(lang)),
                qty=qty,
                prof=discipline_icon(r.profession),
                rank=rank,
            ).rstrip()
        )
        parts = []
        for item, need in r.ingredients.items():
            have = need - lacking.get(item, 0)
            parts.append(f"{have}/{need} {escape(c.items[item].label(lang))}")
        lines.append("      " + " + ".join(parts))
        lines[-2] += f" · /r_{key}"
        if not locked and not lacking:
            ready.append(btn(t(lang, "btn.make", item=c.items[out_key].name.get(lang)), cb("craft", key, n)))
    rows = grid(ready)
    rows.append(
        [
            btn(t(lang, "btn.recipes"), cb("rcl")),
            btn(t(lang, "btn.professions"), cb("prof")),
            btn(t(lang, "btn.back"), cb("scene")),
        ]
    )
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


RECIPE_FILTERS = ("can", "missing", "learn", "t0", "t1")  # /recipes tabs
RECIPES_PER_PAGE = 8


def _origin(item_key: str, lang: str) -> str:
    """Where a missing ingredient comes from: a place, a discipline that refines it, or who sells it."""
    c = get_content()
    out = [
        loc.name.get(lang)
        for loc in c.locations.values()
        if any(r.item == item_key for g in loc.gathering for r in g.resources)
    ]
    out += [discipline_label(r.profession, lang) for r in c.recipes.values() if item_key in r.outputs]
    out += [
        f"{creature_icon(m)} {m.name.get(lang)}"
        for m in c.monsters.values()
        if any(x.item == item_key for x in [*m.loot, *m.harvest])
    ]
    out += [f"🛒 {n.name.get(lang)}" for n in c.npcs.values() if n.shop and item_key in n.shop.items]
    return ", ".join(dict.fromkeys(out))


def _recipe_title(key: str, lang: str) -> str:
    c = get_content()
    r = c.recipes[key]
    out_key, qty = next(iter(r.outputs.items()))
    return f"{c.items[out_key].label(lang)} ×{qty}" + (f" · {t(lang, 'craft.tier', tier=r.tier)}" if r.tier else "")


async def recipe_card(session: AsyncSession, char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """/r_<recipe>: what it makes, from what, where, and the buttons to make one, five or as many as fit."""
    c = get_content()
    r = c.recipes.get(key)
    if r is None:
        return t(lang, "craft.err.unknown"), markup([[btn(t(lang, "btn.back"), cb("crf"))]])
    station = crafting.station_of(r)
    rank = crafting.rank_in(char, r.profession)
    lines = [
        f"<b>{escape(_recipe_title(key, lang))}</b>",
        f"<i>{escape(discipline_label(r.profession, lang))} · {t(lang, 'prof.rank_n', rank=r.min_rank)}</i>",
        RULE,
        _station_place(station, lang),
    ]
    if rank < r.min_rank:
        lines.append(
            t(lang, "craft.locked_why", prof=escape(discipline_label(r.profession, lang)), rank=r.min_rank, yours=rank)
        )
    lacking = await crafting.missing(session, char, r)
    lines += ["", f"<b>{t(lang, 'craft.needs')}</b>"]
    for item, need in r.ingredients.items():
        have = need - lacking.get(item, 0)
        mark = "▫️" if lacking.get(item) else "✅"
        line = f"{mark} {have}/{need} {escape(c.items[item].label(lang))} · /item_{item}"
        origin = _origin(item, lang) if lacking.get(item) else ""
        lines.append(line + (f"\n      <i>{escape(origin)}</i>" if origin else ""))
    lines += ["", t(lang, "craft.gives_xp", xp=r.xp, prof=escape(discipline_label(r.profession, lang)))]
    out_key = next(iter(r.outputs))
    stats = item_stats(out_key, lang)
    if stats:
        lines.append(t(lang, "item.use", what=escape(stats)))
    if c.items[out_key].min_level > 1:
        lines.append(t(lang, "craft.needs_level", level=c.items[out_key].min_level))
    rows = []
    if rank >= r.min_rank and not lacking:
        fits = [await inventory.count(session, char, i) // q for i, q in r.ingredients.items()]
        most = min(get_settings().craft_batch_max, *fits)
        n = nonce()
        rows = [
            [
                btn(t(lang, "btn.make_n", n=qty), cb("craft", f"{key}:{qty}", n))
                for qty in dict.fromkeys(x for x in (1, 5, most) if 1 <= x <= most)
            ]
        ]
    rows.append([btn(t(lang, "btn.recipes"), cb("rcl")), btn(t(lang, "btn.back"), cb("crf"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


async def recipes_list(
    session: AsyncSession, char: Character, lang: str, arg: str = ""
) -> tuple[str, InlineKeyboardMarkup]:
    """/recipes: every recipe of your disciplines, by tab (can make, missing materials, to learn, T0, T1)."""
    c = get_content()
    filt, _, page_s = arg.partition(":")
    filt = filt if filt in RECIPE_FILTERS else "can"
    page = int(page_s) if page_s.isdigit() else 0
    mine = crafting.disciplines(char)
    rows_data = []
    for key, r in c.recipes.items():
        if r.quest is not None:
            continue
        locked = r.profession not in mine or crafting.rank_in(char, r.profession) < r.min_rank or r.special
        lacking = {} if locked else await crafting.missing(session, char, r)
        state = "learn" if locked else ("missing" if lacking else "can")
        if filt in ("t0", "t1") and r.tier != int(filt[1]):
            continue
        if filt in ("can", "missing", "learn") and state != filt:
            continue
        rows_data.append((key, r, state, lacking))
    pages = max(1, -(-len(rows_data) // RECIPES_PER_PAGE))
    page = min(page, pages - 1)
    chunk = rows_data[page * RECIPES_PER_PAGE : (page + 1) * RECIPES_PER_PAGE]
    lines = [t(lang, "craft.list_title"), t(lang, f"craft.filter.{filt}_on", n=len(rows_data)), RULE]
    if not chunk:
        lines.append(t(lang, "craft.list_empty"))
    for key, r, state, lacking in chunk:
        mark = {"can": "✅", "missing": "❌", "learn": "🔒"}[state]
        lines.append(f"{mark} <b>{escape(_recipe_title(key, lang))}</b> · {discipline_icon(r.profession)} · /r_{key}")
        if state == "missing":
            lines.append(
                "      "
                + t(
                    lang,
                    "craft.short_of",
                    items=escape(", ".join(f"{q} {c.items[i].label(lang)}" for i, q in lacking.items())),
                )
            )
    tabs = [btn(t(lang, f"craft.filter.{f}"), cb("rcl", f)) for f in RECIPE_FILTERS if f != filt]
    rows = grid(tabs)
    if pages > 1:
        nav = []
        if page:
            nav.append(btn("◀", cb("rcl", f"{filt}:{page - 1}")))
        if page + 1 < pages:
            nav.append(btn("▶", cb("rcl", f"{filt}:{page + 1}")))
        rows.append(nav)
    rows.append([btn(t(lang, "btn.professions"), cb("prof")), btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def _spec_effect(spec, lang: str) -> str:
    """ "raro ×1,25" or "20 % de una unidad extra": the branch's promise, in the player's words."""
    e = spec.effects
    if e.rare_rel:
        return t(lang, "spec.effect_rare", factor=f"{1 + e.rare_rel:.2f}".rstrip("0").rstrip("."))
    if e.extra_chance:
        return t(lang, "spec.effect_extra", pct=round(e.extra_chance * 100))
    return t(lang, "spec.effect_time", pct=round(e.time_pct * 100))


async def tools_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """🧰 The specialized tool in use for each discipline, and the ones you could switch to."""
    c = get_content()
    lines = [t(lang, "tool.title"), t(lang, "tool.intro"), RULE]
    rows, n = [], nonce()
    for skill in gathering.GATHER_SKILLS:
        rank = gathering.rank_for(characters.mastery_xp(char, skill))
        lines.append(
            t(
                lang,
                "tool.skill",
                icon=MASTERY_ICON.get(skill, "🛠️"),
                skill=escape(characters.mastery_name(skill)[lang]),
                rank=rank,
            )
        )
        chosen = activities.chosen_tool(char, skill)
        designs = activities.tools_for(skill)
        if not chosen:
            base = next((p.base for p in designs.values() if p.base), None)
            if base:
                lines.append(t(lang, "tool.line_base", item=escape(c.items[base].label(lang))))
        for key, profile in designs.items():
            effect = _tool_effect(profile, lang)
            if key == chosen:
                lines.append(t(lang, "tool.line_on", item=escape(c.items[key].label(lang)), effect=effect))
                continue
            owned = await inventory.count(session, char, key) > 0
            state = (
                ""
                if owned and rank >= profile.min_rank
                else t(lang, "tool.locked", rank=profile.min_rank)
                if rank < profile.min_rank
                else t(lang, "tool.not_owned")
            )
            lines.append(
                t(lang, "tool.line_off", item=escape(c.items[key].label(lang)), effect=effect, state=state).rstrip()
            )
            if owned and rank >= profile.min_rank:
                rows.append(btn(c.items[key].label(lang), cb("toolc", key, n)))
    kb = grid(rows)
    kb.append([btn(t(lang, "btn.professions"), cb("prof")), btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(kb)


def _tool_effect(profile, lang: str) -> str:
    if profile.rare_rel:
        return t(lang, "spec.effect_rare", factor=f"{1 + profile.rare_rel:.2f}".rstrip("0").rstrip("."))
    if profile.extra_chance:
        return t(lang, "spec.effect_extra", pct=round(profile.extra_chance * 100))
    return t(lang, "spec.effect_time", pct=round(profile.time_pct * 100))


def specializations_view(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """🌿 The two branches of each mastery: the one in force, the paused one, and what each is worth."""
    settings = get_settings()
    lines = [
        t(lang, "spec.title"),
        t(lang, "spec.intro", rank=specializations.MIN_RANK, cost=settings.spec_switch_cost),
        RULE,
    ]
    rows, n = [], nonce()
    for skill in gathering.GATHER_SKILLS:
        yours = gathering.rank_for(characters.mastery_xp(char, skill))
        name = escape(characters.mastery_name(skill)[lang])
        icon = MASTERY_ICON.get(skill, "🛠️")
        ready = yours >= specializations.MIN_RANK
        lines.append(
            t(
                lang,
                "spec.open" if ready else "spec.locked",
                icon=icon,
                skill=name,
                rank=specializations.MIN_RANK,
                yours=yours,
            )
        )
        for key, spec in specializations.branches(skill).items():
            effect = _spec_effect(spec, lang)
            if specializations.active(char, skill) == key:
                lines.append(t(lang, "spec.branch_on", spec=escape(spec.name.get(lang)), effect=effect))
                continue
            state = t(lang, "spec.paused_tag") if key in specializations.learned(char) else ""
            lines.append(
                t(lang, "spec.branch_off", spec=escape(spec.name.get(lang)), effect=effect, state=state).rstrip()
            )
            if ready:
                rows.append(btn(f"{icon} {spec.name.get(lang)}", cb("specc", key, n)))
    kb = grid(rows)
    kb.append([btn(t(lang, "btn.professions"), cb("prof")), btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(kb)
