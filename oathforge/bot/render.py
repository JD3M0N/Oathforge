"""Message text + keyboards. HTML parse mode; every dynamic string is escaped."""

import re
from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.ai.client import usage_today
from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine.checks import modifier, proficiency_bonus
from oathforge.engine import gathering
from oathforge.engine.combat import EncounterState, available_bonus_actions, valid_targets
from oathforge.engine.progression import MAX_LEVEL, XP_THRESHOLDS, skill_rank
from oathforge.i18n import t
from oathforge.services import (
    actions, activities, bestiary, characters, chronicles, combat_service, crafting, exploration, inventory, npcs, professions,
    quests, world_map,
)
from oathforge.services.events import Outcome, render_event

MAX_MESSAGE = 4000


def hp_bar(hp: int, max_hp: int, width: int = 8) -> str:
    filled = round(width * hp / max_hp) if max_hp else 0
    return "▰" * filled + "▱" * (width - filled)


# level-up events leave the bullet list and get a card of their own (level_up_cards)
LEVEL_KEYS = {"progress.level_up", "progress.new_ability", "progress.asi", "progress.specialization_soon"}
ABILITY_ICON = {"strike": "⚔️", "spell": "🔮", "turn": "☀️", "buff": "🎶", "surge": "💢", "heal": "💚",
                "hide": "🥷", "save": "🌀", "curse": "🕯️", "passive": "🌟"}


def panel_only(key: str) -> bool:
    """Blow-by-blow combat logs: the combat panel (sent right after) already shows them."""
    return key.startswith("combat.") and key not in ("combat.start", "combat.defeat_penalty", "combat.defeat_penalty_free") \
        and not key.startswith("combat.err.")


END_RESULT = {"won": "victory", "fled": "fled", "lost": "defeat"}


def activity_title(act, lang: str) -> str | None:
    """"Rastreo en Prado de los Colmillos · 🏆 Victoria" for an activity that ended in a fight."""
    outcome = (act.result or {}).get("outcome", "")
    result = END_RESULT.get(outcome.rpartition("_")[2])
    if result is None:
        return None
    return f"{activities.describe(act, lang)} · {REPORT_ICON.get(result, '')} {t(lang, 'report.result.' + result)}"


def activity_result(outcome: Outcome, skill: str, lang: str, chronicle: str | None = None,
                    footer: str | None = None, title: str | None = None) -> str:
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


def outcome_text(outcome: Outcome, lang: str, narration: str | None = None) -> str:
    parts: list[str] = []
    if narration:
        parts.append(f"<i>{escape(narration)}</i>")
    for ev in outcome.events:
        if ev.key in LEVEL_KEYS or panel_only(ev.key):
            continue
        line = escape(render_event(ev, lang))
        parts.append(line if ev.key == "text" else f"• {line}")
    return "\n\n".join(p for p in parts if p)[:MAX_MESSAGE]


def ability_tags(a, lang: str) -> str:
    """'pasiva' or 'acción adicional · 2 usos/descanso'."""
    if a.kind == "passive" or a.action == "none":
        return t(lang, "ability.passive")
    tags = [t(lang, f"ability.action.{a.action}")]
    tags.append(t(lang, "ability.uses_one" if a.uses == 1 else "ability.uses", n=a.uses) if a.uses
                else t(lang, "ability.unlimited"))
    return " · ".join(tags)


def ability_block(a, lang: str, prefix: str = "", key: str | None = None) -> list[str]:
    """Name, tags and description of a class ability, as in the level-up card and /class_<key>."""
    icon = ABILITY_ICON.get(a.kind, "✨")
    link = f" · /skill_{key}" if key else ""
    return [f"{prefix}{icon} <b>{escape(a.name.get(lang))}</b> · {ability_tags(a, lang)}",
            f"      <i>{escape(a.description.get(lang))}</i>{link}"]


def ability_mechanics(a, lang: str) -> list[str]:
    """What the engine does with an ability, read from its data (classes.yaml)."""
    c = get_content()
    out = [t(lang, f"skill.kind.{a.kind}")]
    dmg = lambda typ: t(lang, "dmg." + typ) if typ else ""  # noqa: E731
    if a.damage:
        out.append(t(lang, "skill.damage", dice=a.damage, type=dmg(a.damage_type)))
    if a.extra_damage:
        out.append(t(lang, "skill.extra_damage", dice=a.extra_damage, type=dmg(a.damage_type)))
    if a.auto_hit:
        out.append(t(lang, "skill.auto_hit"))
    if a.save:
        out.append(t(lang, "skill.save", ability=c.abilities[a.save].short.get(lang)))
        if a.half_on_save:
            out.append(t(lang, "skill.half_on_save"))
    if a.area == "row":
        out.append(t(lang, "skill.row"))
    if a.targets_type:
        out.append(t(lang, "skill.targets", type=t(lang, "creature." + a.targets_type)))
    if a.heal_per_level:
        out.append(t(lang, "skill.heal_per_level", n=a.heal_per_level))
    if a.heal_dice:
        out.append(t(lang, "skill.heal_dice", dice=a.heal_dice) + (t(lang, f"skill.plus_{a.heal_add}") if a.heal_add else ""))
    if a.temp_hp:
        out.append(t(lang, "skill.temp_hp", dice=a.temp_hp) + (t(lang, f"skill.plus_{a.heal_add}") if a.heal_add else ""))
    if a.status:
        out.append(t(lang, "skill.status", status=t(lang, "status." + a.status), turns=a.status_turns))
    if a.ac_bonus:
        out.append(t(lang, "skill.ac", n=a.ac_bonus))
    if a.ac_bonus_unarmored:
        out.append(t(lang, "skill.ac_unarmored", n=a.ac_bonus_unarmored))
    if a.immune:
        out.append(t(lang, "skill.immune", list=", ".join(t(lang, "status." + s) for s in a.immune)))
    if a.spell_damage_bonus:
        out.append(t(lang, "skill.spell_damage_bonus"))
    if a.sneak_dice:
        out.append(t(lang, "skill.sneak", list=" · ".join(
            t(lang, "skill.sneak_level", n=n, level=lvl) for lvl, n in sorted(a.sneak_dice.items()))))
    if a.extra_attack:
        out.append(t(lang, "skill.extra_attack"))
    if a.halve_first_hit:
        out.append(t(lang, "skill.halve_first_hit"))
    if a.crit_range:
        out.append(t(lang, "skill.crit_range", n=a.crit_range))
    if a.bonus_damage:
        out.append(t(lang, "skill.bonus_damage", dice=a.bonus_damage, type=dmg(a.bonus_damage_type)))
    return [escape(line) for line in out]


def skill_page(key: str, lang: str, char: Character | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """/skill_<key>: a class ability in depth (what the engine does with it). Extra Attack is in two classes."""
    c = get_content()
    owners = [(ck, cl) for ck, cl in c.classes.items() if key in cl.abilities]
    if not owners:
        text, kb = classes_list(lang)
        return t(lang, "skill.unknown") + "\n\n" + text, kb
    a = owners[0][1].abilities[key]
    lines = [f"{ABILITY_ICON.get(a.kind, '✨')} <b>{escape(a.name.get(lang))}</b>",
             " · ".join(f"{CLASS_ICONS.get(ck, '•')} {escape(cl.name.get(lang))} "
                        f"({t(lang, 'classes.level', level=cl.abilities[key].level)})" for ck, cl in owners),
             ability_tags(a, lang), RULE,
             f"<i>{escape((a.details or a.description).get(lang))}</i>", "",
             f"<b>{t(lang, 'skill.mechanics')}</b>", *(f"• {line}" for line in ability_mechanics(a, lang))]
    if char is not None and char.class_key in dict(owners):
        level = dict(owners)[char.class_key].abilities[key].level
        lines += ["", t(lang, "skill.yours" if level <= char.level else "skill.locked", level=level)]
    rows = [[btn(f"{CLASS_ICONS.get(ck, '•')} {cl.name.get(lang)}", cb("cls", ck)) for ck, cl in owners]]
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def level_up_cards(outcome: Outcome, lang: str) -> list[str]:
    """One message per level gained: HP before → after, attribute boost and each new ability explained."""
    c = get_content()
    cards: list[str] = []
    pending: list = []
    for ev in outcome.events:
        if ev.key not in LEVEL_KEYS:
            continue
        if ev.key == "progress.specialization_soon" and cards:  # comes after its level_up
            cards[-1] += "\n\n" + escape(render_event(ev, lang))
            continue
        pending.append(ev)
        if ev.key != "progress.level_up":
            continue
        p = ev.params
        lines = [t(lang, "level_card.title", level=p["level"]), RULE,
                 t(lang, "level_card.hp", prev=p.get("prev_max_hp", p["max_hp"]), max_hp=p["max_hp"],
                   gain=p["max_hp"] - p.get("prev_max_hp", p["max_hp"]))]
        cls_key = p.get("cls")
        for e in pending:
            if e.key == "progress.asi":
                lines.append("💪 " + escape(render_event(e, lang)))
            elif e.key == "progress.new_ability":
                a = c.classes[cls_key].abilities.get(e.params.get("ability_key")) if cls_key in c.classes else None
                if a is None:
                    lines.append(escape(render_event(e, lang)))
                else:
                    lines += ["", t(lang, "level_card.new"), *ability_block(a, lang, key=e.params.get("ability_key"))]
        if cls_key:
            lines += ["", t(lang, "level_card.class", cmd=f"/class_{cls_key}")]
        cards.append("\n".join(lines)[:MAX_MESSAGE])
        pending = []
    return cards


def status_line(char: Character, lang: str) -> str:
    night = exploration.is_night()
    tod = t(lang, "scene.night" if night else "scene.day", clock=exploration.clock(),
            minutes=exploration.until_switch())
    injured = " · " + t(lang, "sheet.injured") if char.conditions.get("injured") else ""
    return t(lang, "scene.status", time=tod, hp=char.hp, max_hp=char.max_hp, gold=char.gold) + injured


# ---------------------------------------------------------------- scene

async def scene(session: AsyncSession, char: Character, lang: str,
                started: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    loc = c.locations[char.location]
    night = exploration.is_night()
    present = exploration.npcs_present(char.location)
    lines = [f"📍 <b>{escape(loc.name.get(lang))}</b>", status_line(char, lang), ""]
    desc = loc.night.get(lang) if night and loc.night else loc.description.get(lang)
    lines.append(escape(desc))
    for extra in await quests.location_texts(session, char):
        lines += ["", f"<i>{escape(extra[lang])}</i>"]
    if present:
        lines += ["", t(lang, "scene.people")]
        lines += [f"• {escape(c.npcs[k].name.get(lang))} <i>({escape(c.npcs[k].title.get(lang))})</i>" for k in present]
    lines += ["", f"<i>{t(lang, 'scene.hint')}</i>"]

    n = nonce()
    act = await activities.open_activity(session, char)
    if act is not None and act.status == "running":
        return activity_panel(char, act, lines, n, lang, started)
    buttons = [btn(t(lang, "btn.travel"), cb("trv")), btn(t(lang, "btn.investigate"), cb("look", "-", n))]
    if present:
        buttons.append(btn(t(lang, "btn.talk"), cb("talkm")))
    if any(c.npcs[k].shop for k in present):
        buttons.append(btn(t(lang, "btn.shop"), cb("shopm")))
    if loc.hunting:
        buttons.append(btn(t(lang, "btn.hunt_night" if night and loc.night_encounters else "btn.hunt"),
                           cb("hunt", "-", n)))
    for kind, skill in activities.options(char):
        label = {"gather": f"btn.gather_{skill}", "stay": "btn.stay", "track": "btn.track"}[kind]
        buttons.append(btn(t(lang, label, minutes=gathering.SECONDS[kind] // 60), cb("act", f"{kind}:{skill}", n)))
    if loc.stations:
        buttons.append(btn(t(lang, "btn.craft"), cb("crf")))
    if loc.guild:
        buttons.append(btn(t(lang, "btn.professions"), cb("prof")))
    if loc.rest_cost is not None:
        buttons.append(btn(t(lang, "btn.rest", cost=loc.rest_cost), cb("rest", "-", n)))
    if loc.healer is not None:
        buttons.append(btn(t(lang, "btn.heal"), cb("heal", "-", n)))  # free during the beta
    if loc.hub and c.media.zone_images(loc.zone, night):
        buttons.append(btn(t(lang, "btn.view_city"), cb("city")))
    rows = grid(buttons)
    trip_to = exploration.trip(char) if char.state == "idle" else None
    if trip_to:  # an ambush stopped the trip halfway: carry on in one tap
        rows.insert(0, [btn(t(lang, "btn.continue_trip", place=c.locations[trip_to].name.get(lang)),
                            cb("go", trip_to, n))])
    for a in await quests.available_actions(session, char, present):
        if a.action.npc is None:
            rows.append([btn(a.action.label.get(lang), cb("qa", a.ref, n))])
    return "\n".join(lines), markup(rows)  # inventory, hero and journal live in the fixed keyboard


SKINNING_TOOL = activities.SKINNING_KNIFE
MASTERY_ICON = {"mining": "⛏️", "woodcutting": "🪓", "herbalism": "🌿", "skinning": "🔪", "fishing": "🎣",
                "tracking": "🐾"}


ACTIVITY_ICON = {**MASTERY_ICON, "rest": "🛏️"}


def activity_panel(char: Character, act, lines: list[str], n: str, lang: str,
                   started: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """The scene while a field activity runs: what, how long is left, Refresh / Abandon. It ends by itself
    (the bot sends the result), so there is nothing to collect. ``started``: the line of the moment it began."""
    seconds = activities.remaining_seconds(act)
    rest = act.kind == "rest"
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


FIELD_MASTERIES = gathering.MASTERIES


def mastery_lines(char: Character, lang: str, skills: tuple[str, ...] = FIELD_MASTERIES) -> list[str]:
    """⛏️ Minería ★★ · 260/500 XP"""
    out = []
    for skill in skills:
        xp = characters.mastery_xp(char, skill)
        out.append(f"{MASTERY_ICON[skill]} {escape(t(lang, f'mastery.name.{skill}'))} "
                   f"{_stars(gathering.rank_for(xp))} · {_progress(xp)}")
    return out


def hobby_lines(char: Character, lang: str) -> list[str]:
    """Cooking and fishing: optional, no slot."""
    c = get_content()
    return [t(lang, "prof.line", icon=c.professions[k].icon, name=escape(c.professions[k].name.get(lang)),
              stars=_stars(professions.rank(char, k)), progress=_progress(professions.xp(char, k)))
            + f" · /prof_{k}" for k in professions.hobbies()]


def _stars(rank: int) -> str:
    return "★" * rank + "☆" * (gathering.MAX_RANK - rank)


def _progress(xp: int) -> str:
    nxt = gathering.next_threshold(xp)
    return f"{xp}/{nxt} XP" if nxt else f"{xp} XP"


def professions_line(char: Character, lang: str) -> str:
    """🛠️ Oficios 1/2: Alquimia ★☆☆☆☆"""
    c = get_content()
    mine = professions.active(char)
    names = ", ".join(f"{c.professions[k].icon} {c.professions[k].name.get(lang)} {_stars(professions.rank(char, k))}"
                      for k in mine) or t(lang, "sheet.no_professions")
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
            lines.append(t(lang, "prof.line", icon=prof.icon, name=escape(prof.name.get(lang)),
                           stars=_stars(professions.rank(char, key)), progress=_progress(xp))
                         + ("" if key in mine else " " + t(lang, "prof.inactive")) + f" · /prof_{key}")
    others = [f"{p.icon} /prof_{k}" for k, p in c.professions.items()
              if not p.hobby and k not in mine and not professions.xp(char, k)]
    if others:
        lines += ["", t(lang, "prof.guides", list=" · ".join(others))]
    lines += ["", t(lang, "prof.hobbies"), *hobby_lines(char, lang)]
    lines += ["", t(lang, "prof.masteries"), *mastery_lines(char, lang), ""]
    rows = []
    if c.locations[char.location].guild:
        lines.append(t(lang, "prof.guild_hint", cost=professions.SWAP_COST))
        n = nonce()
        full = len(mine) >= professions.SLOTS
        learnable = [btn(t(lang, "btn.swap_for" if full else "btn.learn", prof=f"{p.icon} {p.name.get(lang)}",
                           cost=professions.SWAP_COST),
                         cb("profsw", k) if full else cb("plearn", k, n))
                     for k, p in c.professions.items() if k not in mine and not p.hobby]
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
        lines += [head, f"<i>{escape(prof.description.get(lang))}</i>", *_where(prof, lang),
                  t(lang, "hobby.guide", link=f"/prof_{k}"), ""]
    rows = [crafts_tabs(lang, "hob")] if char is not None else [[btn(t(lang, "btn.tab_masteries"), cb("mst"))]]
    return "\n".join(lines).rstrip()[:MAX_MESSAGE], markup(rows)


def swap_menu(char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Which active profession to drop for ``key``; the next step asks to confirm."""
    c = get_content()
    if key not in c.professions:
        return professions_view(char, lang)
    rows = [[btn(t(lang, "btn.replace", prof=c.professions[old].name.get(lang)), cb("profcf", f"{key}:{old}"))]
            for old in professions.active(char)]
    rows.append([btn(t(lang, "btn.back"), cb("prof"))])
    return t(lang, "prof.swap_title", prof=escape(c.professions[key].name.get(lang)), cost=professions.SWAP_COST), markup(rows)


def swap_confirm(char: Character, arg: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Drop one profession for another: the cost and a Confirm button."""
    c = get_content()
    key, _, old = arg.partition(":")
    if key not in c.professions or old not in professions.active(char):
        return professions_view(char, lang)
    text = t(lang, "prof.swap_confirm", old=escape(c.professions[old].name.get(lang)),
             prof=escape(c.professions[key].name.get(lang)), cost=professions.SWAP_COST, gold=char.gold)
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
    lines = [f"{prof.icon} <b>{escape(prof.name.get(lang))}</b>"
             + (f" · {t(lang, 'prof.hobby_tag')}" if prof.hobby else ""),
             f"<i>{escape(prof.description.get(lang))}</i>", RULE]
    if prof.guide:
        guide = RULE_NUMBER.sub(lambda m: str(rule_numbers().get(m.group(1), m.group(0))), prof.guide.get(lang))
        lines += [escape(guide), ""]
    lines += _where(prof, lang)
    if char is not None and (prof.hobby or key in professions.active(char) or professions.xp(char, key)):
        lines.append(t(lang, "prof.your_rank", stars=_stars(professions.rank(char, key)),
                       progress=_progress(professions.xp(char, key))))
    recipes = sorted((r for r in c.recipes.values() if r.profession == key), key=lambda r: r.min_rank)
    if recipes:
        lines += [RULE, f"<b>{t(lang, 'prof.recipes')}</b>"]
    for r in recipes:
        mark = ("✅ " if professions.rank(char, key) >= r.min_rank else "🔒 ") if char is not None else ""
        outs = ", ".join(f"{c.items[i].name.get(lang)} ×{q}" for i, q in r.outputs.items())
        ins = " + ".join(f"{q} {c.items[i].name.get(lang)}" for i, q in r.ingredients.items())
        lines.append(f"{mark}<b>{t(lang, 'prof.rank_n', rank=r.min_rank)}</b> · {escape(outs)}")
        lines.append(f"      ← {escape(ins)}")
    rows = [[btn(t(lang, "btn.professions"), cb("prof"))]] if char is not None else []
    return "\n".join(lines)[:MAX_MESSAGE], (markup(rows) if rows else None)


async def craft_menu(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Recipes of your professions at this station: what you have, what is missing, and a button when ready."""
    c = get_content()
    lines = [t(lang, "craft.title", place=escape(c.locations[char.location].name.get(lang))), ""]
    recipes = crafting.recipes_here(char)
    n = nonce()
    ready = []
    if not recipes:
        lines.append(t(lang, "craft.none"))
        for k in professions.usable(char):
            prof = c.professions[k]
            if prof.station is not None:
                lines.append(f"{prof.icon} {escape(prof.name.get(lang))}: {_station_place(prof.station, lang)}")
    for key, r in recipes.items():
        prof = c.professions[r.profession]
        locked = professions.rank(char, r.profession) < r.min_rank
        lacking = await crafting.missing(session, char, r)
        mark = "🔒" if locked else "❌" if lacking else "✅"
        out_key, qty = next(iter(r.outputs.items()))
        rank = t(lang, "craft.locked", rank=r.min_rank) if locked else ""
        lines.append(t(lang, "craft.recipe", mark=mark, item=escape(c.items[out_key].name.get(lang)), qty=qty,
                       prof=prof.icon, rank=rank).rstrip())
        parts = []
        for item, need in r.ingredients.items():
            have = need - lacking.get(item, 0)
            parts.append(f"{have}/{need} {escape(c.items[item].name.get(lang))}")
        lines.append("      " + " + ".join(parts))
        if not locked and not lacking:
            ready.append(btn(t(lang, "btn.make", item=c.items[out_key].name.get(lang)), cb("craft", key, n)))
    rows = grid(ready)
    rows.append([btn(t(lang, "btn.professions"), cb("prof")), btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def settings_view(user, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """⚙️ Settings: language and manual rolls (off by default; the die is decoration)."""
    on = actions.manual_rolls(user)
    text = t(lang, "settings.text", language=t(lang, "settings.language_name"),
             rolls=t(lang, "roll.on" if on else "roll.off"))
    rows = [[btn("🇪🇸 Español", cb("setl", "es")), btn("🇬🇧 English", cb("setl", "en"))],
            [btn(t(lang, "btn.roll_off" if on else "btn.roll_on"), cb("rollset", "off" if on else "on"))]]
    return text, markup(rows)


def zone_caption(zone_key: str, lang: str) -> str:
    """Caption for the zone's images ("View city"): name and day/night description."""
    zone = get_content().zones[zone_key]
    desc = zone.night if exploration.is_night() and zone.night else zone.description
    return f"🏙️ <b>{escape(zone.name.get(lang))}</b>\n\n{escape(desc.get(lang))}"


def _place_activities(loc_key: str, lang: str) -> str:
    """🛒 Tienda de Mira · 🛏️ Descanso largo (5 🪙) · 💬 Bram"""
    parts = []
    for key, params in world_map.activities(loc_key, exploration.npcs_present(loc_key)):
        params = {k: v.get(lang, v.get("en")) if isinstance(v, dict) else v for k, v in params.items()}
        parts.append(t(lang, f"map.do.{key}", **{k: escape(str(v)) for k, v in params.items()}))
    return " · ".join(parts)


def _route_lines(char: Character, route: world_map.Route, lang: str) -> list[str]:
    """• <b>Capilla del Alba</b> · 4 min · 400 yd · por Plaza  (and what there is to do below)"""
    c = get_content()
    loc = c.locations[route.to]
    tags = [t(lang, "map.route", minutes=route.minutes, yards=route.yards)]
    if route.via:
        tags.append(t(lang, "map.via", places=escape(", ".join(c.locations[k].name.get(lang) for k in route.via))))
    if loc.hub and loc.zone == c.locations[char.location].zone:
        tags.append(t(lang, "map.gate"))
    if world_map.cleared(char, route.to):
        tags.append(t(lang, "map.cleared"))
    lines = [f"• <b>{escape(loc.name.get(lang))}</b> · " + " · ".join(tags) + (" " + "⚠️" * route.danger
                                                                              if route.danger else "")]
    todo = _place_activities(route.to, lang)
    if todo:
        lines.append(f"      {todo}")
    return lines


ZONE_ICON = {"city": "🏙️", "wilds": "🌲", "dungeon": "🕯️"}
ZONE_INLINE = 2  # another zone with more known places than this gets one button that opens it


def _go_button(route: world_map.Route, lang: str, n: str, icon: str = "🧭") -> list:
    name = get_content().locations[route.to].name.get(lang)
    return [btn(f"{icon} {name} · {route.yards} yd {'⚠️' * route.danger}".strip(), cb("go", route.to, n))]


async def map_view(session: AsyncSession, char: Character, lang: str, zone: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """/map and «Travel»: where you are, what there is to do, and every place you can go in one tap (the engine
    walks the way). First your missions, then this zone, then the other zones you know (``zone`` opens one)."""
    c = get_content()
    here = c.locations[char.location]
    zone_here = c.zones[here.zone]
    routes = world_map.destinations(char)
    n = nonce()
    if zone is not None and zone in c.zones:  # one zone's places, from the map's zone button
        z = c.zones[zone]
        lines = [t(lang, "map.zone_title", icon=ZONE_ICON[z.kind], zone=escape(z.name.get(lang))), RULE]
        inside = [r for r in routes if c.locations[r.to].zone == zone]
        for r in inside:
            lines += _route_lines(char, r, lang)
        rows = [] if char.state != "idle" else [_go_button(r, lang, n) for r in inside]
        rows.append([btn(t(lang, "btn.back"), cb("trv"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    lines = [t(lang, "map.title", zone=escape(zone_here.name.get(lang)), kind=t(lang, f"map.kind.{zone_here.kind}")),
             t(lang, "map.here", place=escape(here.name.get(lang)))]
    todo = _place_activities(char.location, lang)
    lines.append(f"      {todo}" if todo else f"      <i>{t(lang, 'map.nothing')}</i>")
    lines.append(RULE)
    rows: list[list] = []

    goals = await exploration.objective_routes(session, char)
    if goals:
        lines.append(t(lang, "map.objective"))
        for quest, r in goals:
            lines.append(t(lang, "map.objective_line", quest=escape(quest.get(lang, quest.get("en"))),
                           place=escape(c.locations[r.to].name.get(lang))))
            rows.append(_go_button(r, lang, n, "📜"))
        lines.append("")

    near = [r for r in routes if c.locations[r.to].zone == here.zone]
    others: dict[str, list[world_map.Route]] = {}
    for r in routes:
        if c.locations[r.to].zone != here.zone:
            others.setdefault(c.locations[r.to].zone, []).append(r)
    if near:
        lines.append(t(lang, f"map.near.{zone_here.kind}"))
        for r in near:
            lines += _route_lines(char, r, lang)
        rows += [_go_button(r, lang, n) for r in near]
    for key, zroutes in others.items():
        z = c.zones[key]
        lines += ["", t(lang, "map.zone_title", icon=ZONE_ICON[z.kind], zone=escape(z.name.get(lang)))]
        if len(zroutes) <= ZONE_INLINE:
            for r in zroutes:
                lines += _route_lines(char, r, lang)
            rows += [_go_button(r, lang, n) for r in zroutes]
        else:
            lines.append("      " + " · ".join(escape(c.locations[r.to].name.get(lang)) for r in zroutes))
            rows.append([btn(t(lang, "btn.zone", icon=ZONE_ICON[z.kind], zone=z.name.get(lang), n=len(zroutes)),
                             cb("trvz", key))])
    far = world_map.beyond(char)
    if far:
        lines += ["", t(lang, "map.beyond")]
        for r in far:
            lines += _route_lines(char, r, lang)
    lines += ["", f"<i>{t(lang, f'map.hint.{zone_here.kind}')}</i>"]
    if char.state != "idle":  # busy with an activity: the map, but no roads to take
        lines += ["", t(lang, "map.busy")]
        return "\n".join(lines)[:MAX_MESSAGE], markup([[btn(t(lang, "btn.back"), cb("scene"))]])
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def talk_menu(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    rows = [[btn(f"💬 {c.npcs[k].name.get(lang)}", cb("talk", k))] for k in exploration.npcs_present(char.location)]
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return t(lang, "talk.title"), markup(rows)


async def conversation(session: AsyncSession, char: Character, npc_key: str, lang: str,
                       line: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    npc = c.npcs[npc_key]
    text = [f"💬 <b>{escape(npc.name.get(lang))}</b>, {escape(npc.title.get(lang))}", ""]
    greeting = npc.greeting
    if not line and npc.greeting_return is not None and await quests.finished_giver(session, char, npc_key):
        greeting = npc.greeting_return
    text.append(escape(line) if line else escape(greeting.get(lang)))
    text += ["", f"<i>{t(lang, 'talk.hint', npc=escape(npc.name.get(lang)))}</i>"]
    n = nonce()
    present = exploration.npcs_present(char.location)
    rows = [[btn(a.action.label.get(lang), cb("qa", a.ref, n))]
            for a in await quests.available_actions(session, char, present, npc=npc_key)]
    if npc.shop:
        rows.append([btn(t(lang, "btn.shop"), cb("shop", npc_key))])
    rows.append([btn(t(lang, "btn.leave"), cb("bye"))])
    return "\n".join(text), markup(rows)


# ---------------------------------------------------------------- shop

def shop_menu(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    rows = [[btn(f"🛒 {c.npcs[k].name.get(lang)}", cb("shop", k))]
            for k in exploration.npcs_present(char.location) if c.npcs[k].shop]
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return t(lang, "shop.choose"), markup(rows)


async def shop(session: AsyncSession, char: Character, npc_key: str, lang: str,
               group: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """A shop: first its categories (weapons, armor...), then the items of the one you pick, to buy."""
    c = get_content()
    npc = c.npcs[npc_key]
    rep = await npcs.reputation_with(session, char, npc.faction)
    n = nonce()
    lines = [t(lang, "shop.title", npc=escape(npc.name.get(lang)), gold=char.gold)]
    groups: dict[str, list[str]] = {}
    for key in npc.shop.items:
        groups.setdefault(_shop_group(c.items[key]), []).append(key)
    rows = []
    if group in groups:
        lines += ["", f"<b>{t(lang, f'shop.group.{group}')}</b>"]
        for key in groups[group]:
            item, price = c.items[key], inventory.buy_price(key, rep)
            stats = item_stats(key, lang)
            lines.append(f"• <b>{escape(item.name.get(lang))}</b>{' · ' + escape(stats) if stats else ''} · {price} 🪙"
                         f" · /item_{key}")
            rows.append([btn(f"{item.name.get(lang)} · {price} 🪙", cb("buy", f"{npc_key}:{key}", n))])
        rows.append([btn(t(lang, "btn.back"), cb("shop", npc_key))])
        return "\n".join(lines), markup(rows)
    lines += ["", f"<i>{t(lang, 'shop.pick_group')}</i>"]
    rows += grid([btn(f"{t(lang, f'shop.group.{g}')} ({len(groups[g])})", cb("shopg", f"{npc_key}:{g}"))
                  for g in SHOP_GROUPS if groups.get(g)])
    if npc.shop.buys:
        rows.append([btn(t(lang, "btn.sell"), cb("sellm", npc_key))])
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines), markup(rows)


SHOP_GROUPS = ("weapons", "armor", "consumables", "tools", "other")


def _shop_group(item) -> str:
    if item.type == "weapon":
        return "weapons"
    if item.type in ("armor", "shield"):
        return "armor"
    return {"consumable": "consumables", "tool": "tools"}.get(item.type, "other")


def item_stats(key: str, lang: str) -> str:
    """What an item does, in a few words: "1d8 cortante", "CA 11 + DES", "2d4+2 PV", "⛏️ Minería"."""
    c = get_content()
    item = c.items[key]
    if item.weapon:
        w = item.weapon
        tags = [t(lang, "shop.stat.ranged")] if w.ranged else [t(lang, "shop.stat.finesse")] if w.finesse else []
        return " · ".join([f"{w.damage} {t(lang, f'dmg.{w.damage_type}')}", *tags])
    if item.base_ac is not None:
        if item.dex_cap == 0:
            return t(lang, "shop.stat.ac", ac=item.base_ac)
        if item.dex_cap is not None and item.dex_cap < 5:
            return t(lang, "shop.stat.ac_dex_cap", ac=item.base_ac, cap=item.dex_cap)
        return t(lang, "shop.stat.ac_dex", ac=item.base_ac)
    if item.ac_bonus:
        return t(lang, "shop.stat.ac_bonus", bonus=item.ac_bonus)
    if item.heal:
        return t(lang, "shop.stat.heal", dice=item.heal)
    for effect in item.effects:
        return t(lang, f"shop.stat.{effect.type}")
    if item.combat is not None:
        return t(lang, "shop.stat.combat")
    for loc in c.locations.values():
        for g in loc.gathering:
            if g.tool == key:
                return f"{MASTERY_ICON[g.skill]} {t(lang, f'mastery.name.{g.skill}')}"
    if key == SKINNING_TOOL:
        return f"{MASTERY_ICON['skinning']} {t(lang, 'mastery.name.skinning')}"
    return ""


ITEM_ICON = {"weapon": "⚔️", "armor": "🛡️", "shield": "🛡️", "consumable": "🧪", "tool": "🧰", "quest": "📜",
             "material": "🧱", "trinket": "💍"}


def item_page(key: str, lang: str) -> str:
    """/item_<key>: what an item is, what it is for, where it comes from and what it is worth."""
    c = get_content()
    item = c.items.get(key)
    if item is None:
        return t(lang, "item.err.unknown")
    lines = [f"{ITEM_ICON[item.type]} <b>{escape(item.name.get(lang))}</b>",
             f"<i>{t(lang, f'item.type.{item.type}')}</i>", RULE, escape(item.description.get(lang))]
    stats = item_stats(key, lang)
    if stats:
        lines += ["", t(lang, "item.use", what=escape(stats))]
    used_in = sorted({c.items[next(iter(r.outputs))].name.get(lang) + f" ({c.professions[r.profession].icon})"
                      for r in c.recipes.values() if key in r.ingredients})
    if used_in:
        lines.append(t(lang, "item.ingredient", list=escape(", ".join(used_in))))
    sources = []
    sources += [loc.name.get(lang) for loc in c.locations.values()
                if any(r.item == key for g in loc.gathering for r in g.resources)]
    sources += [f"{creature_icon(m)} {m.name.get(lang)}" for m in c.monsters.values()
                if any(x.item == key for x in [*m.loot, *m.harvest])]
    sources += [f"{c.professions[r.profession].icon} {c.professions[r.profession].name.get(lang)}"
                for r in c.recipes.values() if key in r.outputs]
    sources += [f"🛒 {n.name.get(lang)}" for n in c.npcs.values() if n.shop and key in n.shop.items]
    sources += [f"📜 {q.name.get(lang)}" for q in c.quests.values()
                if any(key in (eff.get("give_item") or {}) for eff in q.rewards)]
    if sources:
        lines.append(t(lang, "item.sources", list=escape(", ".join(dict.fromkeys(sources)))))
    lines.append("")
    if item.sellable and item.value:
        lines.append(t(lang, "item.value", value=item.value, sell=inventory.sell_price(key, 0)))
    else:
        lines.append(t(lang, "item.no_value"))
    return "\n".join(lines)[:MAX_MESSAGE]


async def sell_menu(session: AsyncSession, char: Character, npc_key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    rep = await npcs.reputation_with(session, char, c.npcs[npc_key].faction)
    n = nonce()
    rows = []
    for inst in await inventory.items_of(session, char):
        item = c.items[inst.item_key]
        if not item.sellable or inst.equipped_slot:
            continue
        price = inventory.sell_price(inst.item_key, rep)
        qty = f" ×{inst.qty}" if inst.qty > 1 else ""
        rows.append([btn(f"{item.name.get(lang)}{qty} → {price} 🪙", cb("sell", f"{npc_key}:{inst.id}", n))])
    rows.append([btn(t(lang, "btn.back"), cb("shop", npc_key))])
    text = t(lang, "shop.sell_title") if len(rows) > 1 else t(lang, "shop.nothing_to_sell")
    return text, markup(rows)


# ---------------------------------------------------------------- character

SLOT_ICONS = {"main_hand": "🗡️", "ranged": "🏹", "off_hand": "🛡️", "body": "🥋"}
RULE = "━━━━━━━━━━━━━━━━"


def rep_label(value: int, lang: str) -> str:
    tier = ("hated" if value <= -50 else "hostile" if value <= -10 else "neutral" if value < 10
            else "friendly" if value < 50 else "honored")
    return t(lang, f"sheet.rep.{tier}")


def _gear_line(inst, lang: str) -> str:
    item = get_content().items[inst.item_key]
    if item.weapon:
        detail = f"{item.weapon.damage} {t(lang, 'dmg.' + item.weapon.damage_type)}"
    elif item.base_ac is not None:
        detail = t(lang, "sheet.armor_ac", ac=item.base_ac)
    elif item.ac_bonus:
        detail = t(lang, "sheet.shield_ac", ac=item.ac_bonus)
    else:
        detail = ""
    detail = f" · <i>{escape(detail)}</i>" if detail else ""
    return f"{SLOT_ICONS.get(inst.equipped_slot, '•')} {escape(item.name.get(lang))}{detail}"


def _sheet_top(c, cls, char: Character, gear: dict, lang: str) -> list[str]:
    """Name, identity, HP/XP bars and vitals: shared by the summary and the full sheet."""
    lines = [
        f"🦸 <b>{escape(char.name)}</b>",
        t(lang, "sheet.identity", level=char.level, cls=cls.name.get(lang)),
        f"<i>{t(lang, 'gender.' + char.gender) + ' · ' if char.gender else ''}"
        f"{escape(c.lineages[char.lineage].name.get(lang))} · "
        f"{escape(characters.background_name(char, lang))}</i>",
        RULE,
        t(lang, "sheet.hp", hp=char.hp, max_hp=char.max_hp, bar=hp_bar(char.hp, char.max_hp)),
    ]
    if char.level < MAX_LEVEL:
        lo, hi = XP_THRESHOLDS[char.level - 1], XP_THRESHOLDS[char.level]
        lines.append(t(lang, "sheet.xp", cur=char.xp - lo, need=hi - lo, level=char.level + 1, xp=char.xp,
                       bar=hp_bar(char.xp - lo, hi - lo)))
    else:
        lines.append(t(lang, "sheet.xp_max", xp=char.xp))
    lines.append(t(lang, "sheet.vitals", ac=characters.armor_class(char, gear), pb=proficiency_bonus(char.level),
                   gold=char.gold))
    if char.conditions.get("injured"):
        lines.append(t(lang, "sheet.injured"))
    return lines


def attribute(key: str, score: int, lang: str, aligned: bool = False) -> str:
    """'💪 STR 16 (+3)': the same look at creation, in /hero and in /sheet (aligned: for a monospace block)."""
    info = get_content().abilities[key]
    short = info.short.get(lang)
    if aligned:
        return f"{info.icon} {short:<3} {score:>2} ({modifier(score):+d})".lstrip()
    return f"{info.icon} {short} {score} ({modifier(score):+d})".lstrip()


def _sheet_attributes(c, cls, char: Character, lang: str) -> list[str]:
    """Ability scores, two per row in a monospace block; ★ marks the class's primary."""
    cells = []
    for a in c.abilities:
        star = "★" if a == cls.primary else " "
        cells.append(attribute(a, char.abilities[a], lang, aligned=True) + star)
    pairs = ["  ".join(cells[i:i + 2]) for i in range(0, len(cells), 2)]
    return ["", f"<b>{t(lang, 'sheet.attributes')}</b>", "<code>" + escape("\n".join(pairs)) + "</code>"]


def _sheet_gear(gear: dict, lang: str) -> list[str]:
    order = ("main_hand", "ranged", "off_hand", "body")
    worn = [gear[slot] for slot in order if slot in gear]
    return ["", f"<b>{t(lang, 'sheet.gear')}</b>",
            *([_gear_line(inst, lang) for inst in worn] or [f"<i>{t(lang, 'sheet.no_gear')}</i>"])]


def _uses(char: Character, key: str, a) -> str:
    uses = char.resources.get(key)
    return f" ({a.uses if uses is None else uses}/{a.uses})" if a.uses else ""


async def hero(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Summary: vitals, attributes, gear and unlocked abilities by name. /sheet has everything."""
    c = get_content()
    cls = c.classes[char.class_key]
    gear = await characters.equipped(session, char)
    lines = _sheet_top(c, cls, char, gear, lang) + _sheet_attributes(c, cls, char, lang) + _sheet_gear(gear, lang)
    unlocked = [escape(a.name.get(lang)) + _uses(char, key, a)
                for key, a in cls.abilities.items() if a.level <= char.level]
    if unlocked:
        lines += ["", f"<b>{t(lang, 'sheet.abilities')}</b>", "✨ " + " · ".join(unlocked)]
    kb = markup([[btn(t(lang, "btn.full_sheet"), cb("sheet"))],
                 [btn(t(lang, "btn.inventory"), cb("inv")), btn(t(lang, "btn.journal"), cb("jr"))],
                 [btn(t(lang, "btn.back"), cb("scene"))]])
    return "\n".join(lines)[:MAX_MESSAGE], kb


def portrait_caption(char: Character, lang: str) -> str:
    """Caption for the class portrait sent before the full sheet."""
    cls = get_content().classes[char.class_key]
    return f"🦸 <b>{escape(char.name)}</b> · {escape(t(lang, 'sheet.identity', level=char.level, cls=cls.name.get(lang)))}"


async def sheet(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The full character sheet: everything the engine knows about the hero."""
    c = get_content()
    cls = c.classes[char.class_key]
    gear = await characters.equipped(session, char)
    skills = await characters.skills_of(session, char)
    lines = _sheet_top(c, cls, char, gear, lang)
    extra = [f"<i>{escape(cls.description.get(lang))}</i>"]
    if char.specialization in cls.specializations:
        extra.insert(0, t(lang, "sheet.specialization", name=escape(cls.specializations[char.specialization].get(lang))))
    lines[2:2] = extra
    lines.append(t(lang, "sheet.hit_die", die=cls.hit_die))
    lines.append(t(lang, "sheet.class_link", cmd=f"/class_{char.class_key}"))
    lines += _sheet_attributes(c, cls, char, lang)

    # combat numbers: attacks, spellcasting, passive perception, immunities
    lines += ["", f"<b>{t(lang, 'sheet.combat')}</b>"]
    for a in characters.attack_profiles(char, gear):
        lines.append(("🏹 " if a.ranged else "🗡️ ") + escape(t(
            lang, "sheet.attack", name=a.name[lang], to_hit=f"{a.to_hit:+d}", damage=a.damage,
            type=t(lang, "dmg." + a.damage_type))))
    if cls.casting:
        _, to_hit, dc = characters.spell_stats(char)
        lines.append("🔮 " + escape(t(lang, "sheet.spellcasting", ability=c.abilities[cls.casting].name.get(lang),
                                      to_hit=f"{to_hit:+d}", dc=dc)))
    lines.append(t(lang, "sheet.passive_perception", value=10 + characters.skill_bonus(char, skills, "perception")))
    immune = characters.immunities(char)
    if immune:
        lines.append(t(lang, "sheet.immune", list=", ".join(t(lang, "status." + s) for s in immune)))

    lines += _sheet_gear(gear, lang)

    # every skill: ● proficient, ○ practiced, · untrained
    lines += ["", f"<b>{t(lang, 'sheet.skills')}</b>"]
    for key, skill in c.skills.items():
        row = skills.get(key)
        mark = "●" if row and row.proficient else "○" if row and row.xp else "·"
        rank = "★" * skill_rank(row.xp) if row else ""
        lines.append(f"{mark} {escape(skill.name.get(lang))} "
                     f"<b>{characters.skill_bonus(char, skills, key):+d}</b> {rank}".rstrip())

    # class abilities: unlocked with uses, locked ones show the level they unlock at
    lines += ["", f"<b>{t(lang, 'sheet.abilities')}</b>"]
    for key, a in cls.abilities.items():
        if a.level <= char.level:
            lines.append(f"✨ <b>{escape(a.name.get(lang))}</b>{_uses(char, key, a)}: {escape(a.description.get(lang))}"
                         f" /skill_{key}")
        else:
            lines.append(f"🔒 <i>{t(lang, 'sheet.locked', level=a.level, name=escape(a.name.get(lang)))}</i>")

    # reputation
    reps = await npcs.reputations(session, char)
    if reps:
        lines += ["", f"<b>{t(lang, 'sheet.reputation')}</b>"]
        for fac, value in reps.items():
            lines.append(f"• {escape(c.factions[fac].name.get(lang))}: {value:+d} · {rep_label(value, lang)}")

    # origins
    lines += ["", f"<b>{t(lang, 'sheet.origins')}</b>",
              f"🧬 <i>{escape(c.lineages[char.lineage].trait_text.get(lang))}</i>",
              f"📖 <i>{escape(characters.background_story(char, lang))}</i>"]

    # professions and gathering masteries
    lines += ["", professions_line(char, lang), "", f"<b>{t(lang, 'sheet.hobbies')}</b>", *hobby_lines(char, lang),
              "", f"<b>{t(lang, 'sheet.masteries')}</b>", *mastery_lines(char, lang)]

    # today's AI budget and expedition chronicles
    limit = get_settings().ai_user_daily_calls
    calls, _ = await usage_today(session, char.user_id)
    left = max(0, limit - calls)
    lines += [RULE, t(lang, "sheet.ai_usage", calls=calls, limit=limit, left=left, bar=hp_bar(left, limit))]
    climit = get_settings().ai_user_daily_chronicles
    cused = await chronicles.chronicles_today(session, char.id)
    cleft = max(0, climit - cused)
    lines.append(t(lang, "sheet.chronicles", used=cused, limit=climit, left=cleft, bar=hp_bar(cleft, climit)))

    kb = markup([[btn(t(lang, "btn.hero_summary"), cb("hero"))],
                 [btn(t(lang, "btn.inventory"), cb("inv")), btn(t(lang, "btn.journal"), cb("jr"))],
                 [btn(t(lang, "btn.back"), cb("scene"))]])
    return "\n".join(lines)[:MAX_MESSAGE], kb


async def inventory_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    n = nonce()
    lines = [t(lang, "inv.title", gold=char.gold), ""]
    rows = []
    # what you wear first, so two copies of the same weapon are easy to tell apart
    for inst in sorted(await inventory.items_of(session, char), key=lambda i: not i.equipped_slot):
        item = c.items[inst.item_key]
        qty = f" ×{inst.qty}" if inst.qty > 1 else ""
        worn = " ✅" if inst.equipped_slot else ""
        lines.append(f"• {escape(item.name.get(lang))}{qty}{worn}: <i>{escape(item.description.get(lang))}</i>"
                     f" · /item_{inst.item_key}")
        if item.slot:
            label = t(lang, "btn.unequip" if inst.equipped_slot else "btn.equip", item=item.name.get(lang))
            label = f"{SLOT_ICONS.get(inst.equipped_slot or item.slot, '')} {label}".strip()
            rows.append([btn(label, cb("eq", str(inst.id), n))])
        elif inventory.effects_of(item):
            rows.append([btn(t(lang, "btn.use", item=item.name.get(lang)), cb("use", inst.item_key, n))])
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


QUEST_ICONS = {"locked": "🔒", "available": "❔", "active": "📜", "completed": "✅", "failed": "❌"}


def _objective_line(obj, done: int, lang: str) -> str:
    target = quests.objective_target(obj)[lang]
    mark = "☑️" if done >= obj.count else "▫️"
    count = f" {done}/{obj.count}" if obj.count > 1 else ""
    return f"{mark} {escape(t(lang, 'quest.objective.' + obj.kind, target=target))}{count}"


async def journal(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The journal hub: the current missions at a glance, then Missions / Bestiary / Rumors."""
    lines = [t(lang, "journal.title"), ""]
    current = [(k, q, p) for k, q, p in await quests.journal(session, char)
               if quests.stage_of(q, p)[1] in ("active", "available")]
    if current:
        lines.append(f"<b>{t(lang, 'journal.current')}</b>")
        for _, quest, prog in current:
            stage, state = quests.stage_of(quest, prog)
            lines.append(f"{QUEST_ICONS[state]} <b>{escape(quest.name.get(lang))}</b>")
            lines.append(f"<i>{escape(quest.stages[stage].journal.get(lang))}</i>")
            lines += [_objective_line(o, n, lang) for o, n in quests.objective_progress(quest, prog)]
            lines.append("")
    else:
        lines += [f"<i>{t(lang, 'journal.no_current')}</i>", ""]
    lines.append(f"<i>{t(lang, 'journal.hint')}</i>")
    kb = markup([[btn(t(lang, "btn.missions"), cb("jrm")), btn(t(lang, "btn.quest_log"), cb("jrl"))],
                 [btn(t(lang, "btn.bestiary"), cb("jrb")), btn(t(lang, "btn.rumors"), cb("jrr"))],
                 [btn(t(lang, "btn.stats"), cb("jrs")), btn(t(lang, "btn.back"), cb("scene"))]])
    return "\n".join(lines)[:MAX_MESSAGE], kb


FINISHED = ("completed", "failed")


async def missions(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """/quests: only what is in progress or on offer; finished missions live in the journal's log."""
    entries = await quests.journal(session, char)
    done = sum(1 for _, q, p in entries if quests.stage_of(q, p)[1] == "completed")
    lines = [t(lang, "journal.missions_title", done=done, total=len(entries)), ""]
    rows = []
    for key, quest, prog in entries:
        _, state = quests.stage_of(quest, prog)
        if state in ("active", "available"):
            rows.append([btn(f"{QUEST_ICONS[state]} {quest.name.get(lang)}", cb("jq", key))])
    lines.append(f"<i>{t(lang, 'journal.missions_hint' if rows else 'journal.no_current')}</i>")
    rows.append([btn(t(lang, "btn.quest_log"), cb("jrl")), btn(t(lang, "btn.back"), cb("jr"))])
    return "\n".join(lines), markup(rows)


def fmt_int(n: int, lang: str) -> str:
    """3.400 in Spanish, 3,400 in English."""
    return f"{n:,}".replace(",", "." if lang == "es" else ",")


def stats_view(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The journal's statistics: how far you walked, where you have been, what you fought."""
    c = get_content()
    st = characters.stats(char)
    places = [p for p in st.get("places", []) if p in c.locations]
    cities = {c.locations[p].zone for p in places if c.zones[c.locations[p].zone].kind == "city"}
    kills = {k: v.get("killed", 0) for k, v in (char.bestiary or {}).items() if v.get("killed")}
    top = sorted(kills.items(), key=lambda kv: -kv[1])[:3]
    lines = [t(lang, "stats.title"), RULE,
             t(lang, "stats.distance", yards=fmt_int(int(st.get("yards", 0)), lang)),
             t(lang, "stats.places", places=len(places), cities=len(cities)),
             t(lang, "stats.battles", won=st.get("battles_victory", 0), lost=st.get("battles_defeat", 0),
               fled=st.get("battles_fled", 0)),
             t(lang, "stats.kills", n=sum(kills.values()))]
    if top:
        lines.append("      " + escape(", ".join(f"{c.monsters[k].name.get(lang)} ×{n}" for k, n in top if k in c.monsters)))
    lines += [t(lang, "stats.dodges", n=st.get("dodges", 0)), t(lang, "stats.crits", n=st.get("crits", 0)),
              t(lang, "stats.activities", n=st.get("activities", 0)), "", f"<i>{t(lang, 'stats.since')}</i>"]
    return "\n".join(lines), markup([[btn(t(lang, "btn.back"), cb("jr"))]])


async def quest_log(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The journal's log: the missions already finished."""
    entries = [(k, q, p) for k, q, p in await quests.journal(session, char) if quests.stage_of(q, p)[1] in FINISHED]
    lines = [t(lang, "journal.log_title", n=len(entries)), ""]
    rows = [[btn(f"{QUEST_ICONS[quests.stage_of(q, p)[1]]} {q.name.get(lang)}", cb("jq", k))] for k, q, p in entries]
    lines.append(f"<i>{t(lang, 'journal.log_hint' if rows else 'journal.log_empty')}</i>")
    rows.append([btn(t(lang, "btn.missions"), cb("jrm")), btn(t(lang, "btn.back"), cb("jr"))])
    return "\n".join(lines), markup(rows)


async def mission(session: AsyncSession, char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    back = markup([[btn(t(lang, "btn.back"), cb("jrm"))]])
    entry = next(((q, p) for k, q, p in await quests.journal(session, char) if k == key), None)
    if entry is None:
        return t(lang, "quest.err.unavailable"), back
    quest, prog = entry
    stage, state = quests.stage_of(quest, prog)
    if state in FINISHED:  # opened from the log: back to it
        back = markup([[btn(t(lang, "btn.back"), cb("jrl"))]])
    if state == "locked":
        lines = [f"🔒 <b>{t(lang, 'journal.locked_name')}</b>", "",
                 f"<i>{escape(quest.stages[stage].journal.get(lang))}</i>"]
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
        (kind, arg), = eff.items()
        if kind == "xp":
            parts.append(f"✨ {arg} XP")
        elif kind == "gold":
            parts.append(f"🪙 {arg}")
        elif kind == "give_item":
            parts += [f"🎁 {c.items[i].name.get(lang)}" + (f" ×{q}" if q > 1 else "") for i, q in arg.items()]
    return " · ".join(escape(p) for p in parts)


# ---------------------------------------------------------------- rulebook

RULE_NUMBER = re.compile(r"\{(\w+)\}")


def rule_numbers() -> dict:
    """{placeholders} in content/rulebook.yaml, straight from the engine, so the rulebook never goes stale."""
    ambush = [g.stay_ambush for loc in get_content().locations.values() for g in loc.gathering if g.stay_ambush]
    return {
        "gather_min": gathering.GATHER_SECONDS // 60, "stay_min": gathering.STAY_SECONDS // 60,
        "track_min": gathering.TRACK_SECONDS // 60, "rest_min": gathering.REST_SECONDS // 60,
        "gather_units": "{}–{}".format(*gathering.GATHER_UNITS), "stay_units": "{}–{}".format(*gathering.STAY_UNITS),
        "ambush": f"{round(min(ambush) * 100)}–{round(max(ambush) * 100)} %" if ambush else "—",
        "prey_pct": round(gathering.TRACK_PREY_CHANCE * 100), "bonus_pct": round(gathering.BONUS_PER_RANK * 100),
        "bonus_cap": round(gathering.BONUS_CAP * 100), "max_rank": gathering.MAX_RANK,
        "slots": professions.SLOTS, "swap_cost": professions.SWAP_COST,
    }


def rulebook(lang: str, key: str | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """/rulebook: an index of sections as buttons; each section a page with ◀ ▶ (edits the same message)."""
    c = get_content()
    keys = list(c.rulebook)
    if key not in c.rulebook:
        lines = [t(lang, "rulebook.title"), RULE, t(lang, "rulebook.intro"), ""]
        lines += [f"{sec.icon} {escape(sec.title.get(lang))}" for sec in c.rulebook.values()]
        buttons = [btn(f"{sec.icon} {sec.title.get(lang)}", cb("rb", k)) for k, sec in c.rulebook.items()]
        return "\n".join(lines)[:MAX_MESSAGE], markup(grid(buttons))
    sec = c.rulebook[key]
    body = RULE_NUMBER.sub(lambda m: str(rule_numbers().get(m.group(1), m.group(0))), sec.body.get(lang))
    lines = [f"{sec.icon} <b>{escape(sec.title.get(lang))}</b>", RULE, escape(body)]
    if key == "abilities":  # the six abilities and what each is for, straight from abilities.yaml
        lines.append("")
        lines += [f"{a.icon} <b>{escape(a.name.get(lang))}</b>: {escape(a.effect.get(lang))}" for a in c.abilities.values()]
    i = keys.index(key)
    nav = [btn(f"◀ {c.rulebook[keys[i - 1]].icon}", cb("rb", keys[i - 1])) if i > 0 else None,
           btn(t(lang, "rulebook.index"), cb("rb", "index")),
           btn(f"{c.rulebook[keys[i + 1]].icon} ▶", cb("rb", keys[i + 1])) if i + 1 < len(keys) else None]
    return "\n".join(lines)[:MAX_MESSAGE], markup([[b for b in nav if b]])


# ---------------------------------------------------------------- lineages and backgrounds

def lineages_list(lang: str) -> str:
    """/lineage: every lineage with its bonuses, skills and trait."""
    c = get_content()
    lines = [t(lang, "lineages.title"), RULE]
    for lin in c.lineages.values():
        bonuses = " · ".join(f"{c.abilities[a].icon} {c.abilities[a].short.get(lang)} {n:+d}"
                             for a, n in lin.bonuses.items())
        lines += [f"{lin.icon} <b>{escape(lin.name.get(lang))}</b>", f"<i>{escape(lin.description.get(lang))}</i>",
                  t(lang, "lineages.bonuses", list=bonuses)]
        if lin.skills:
            lines.append(t(lang, "classes.skills", list=escape(", ".join(c.skills[s].name.get(lang) for s in lin.skills))))
        lines += [f"✨ {escape(lin.trait_text.get(lang))}", ""]
    return "\n".join(lines).rstrip()[:MAX_MESSAGE]


def background_line(bg, lang: str) -> str:
    """'🎓 Athletics, Intimidation · 💰 15 · 🎒 Rope'."""
    c = get_content()
    parts = ["🎓 " + ", ".join(c.skills[s].name.get(lang) for s in bg.skills), f"💰 {bg.gold}"]
    if bg.items:
        parts.append("🎒 " + ", ".join(c.items[i].name.get(lang) + (f" ×{n}" if n > 1 else "")
                                       for i, n in bg.items.items()))
    return escape(" · ".join(parts))


def backgrounds_list(lang: str) -> str:
    """/background: every background with its skills, gold and starting items."""
    c = get_content()
    lines = [t(lang, "backgrounds.title"), RULE]
    for bg in c.backgrounds.values():
        if bg.custom:
            continue
        lines += [f"{bg.icon} <b>{escape(bg.name.get(lang))}</b>", f"<i>{escape(bg.description.get(lang))}</i>",
                  background_line(bg, lang), ""]
    lines.append(t(lang, "backgrounds.custom"))
    return "\n".join(lines).rstrip()[:MAX_MESSAGE]


# ---------------------------------------------------------------- classes

CLASS_ICONS = {"paladin": "🛡️", "rogue": "🗡️", "warrior": "⚔️", "priest": "✝️", "mage": "🔮", "druid": "🌿",
               "bard": "🎻", "warlock": "🕯️"}


def classes_list(lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Every class with its role, hit die and a tappable /class_<key>."""
    c = get_content()
    lines = [t(lang, "classes.title"), RULE]
    for key, cl in c.classes.items():
        lines += [f"{CLASS_ICONS.get(key, '•')} <b>{escape(cl.name.get(lang))}</b> · 🎲 d{cl.hit_die} · /class_{key}",
                  f"<i>{escape(cl.description.get(lang))}</i>", ""]
    lines.append(f"<i>{t(lang, 'classes.hint')}</i>")
    buttons = [btn(f"{CLASS_ICONS.get(key, '•')} {cl.name.get(lang)}", cb("cls", key)) for key, cl in c.classes.items()]
    return "\n".join(lines)[:MAX_MESSAGE], markup(grid(buttons))


def class_page(key: str, lang: str, char: Character | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """A class at a glance: hit die, attributes, skills, starting gear, abilities by level, specializations.

    With the player's own class, unlocked abilities are marked ✅ and the rest 🔒.
    """
    c = get_content()
    if key not in c.classes:
        text, kb = classes_list(lang)
        return t(lang, "classes.unknown") + "\n\n" + text, kb
    cl = c.classes[key]
    mine = char is not None and char.class_key == key
    lines = [f"{CLASS_ICONS.get(key, '•')} <b>{escape(cl.name.get(lang))}</b>",
             f"<i>{escape(cl.description.get(lang))}</i>", RULE,
             t(lang, "classes.hit_die", die=cl.hit_die, hp=cl.hit_die),
             t(lang, "classes.primary", ability=escape(c.abilities[cl.primary].name.get(lang)))]
    if cl.casting:
        lines.append(t(lang, "classes.casting", ability=escape(c.abilities[cl.casting].name.get(lang))))
    lines.append(t(lang, "classes.skills", list=escape(", ".join(c.skills[s].name.get(lang) for s in cl.skills))))
    gear = ", ".join(c.items[i].name.get(lang) + (f" ×{n}" if n > 1 else "") for i, n in cl.items.items())
    lines.append(t(lang, "classes.items", list=escape(gear)))

    lines += [RULE, f"<b>{t(lang, 'classes.abilities')}</b>"]
    for akey, a in sorted(cl.abilities.items(), key=lambda kv: kv[1].level):
        mark = ("✅ " if a.level <= char.level else "🔒 ") if mine else ""
        lines += ["", *ability_block(a, lang, prefix=f"{mark}<b>{t(lang, 'classes.level', level=a.level)}</b> · ", key=akey)]
    if cl.specializations:
        lines += [RULE, t(lang, "classes.specializations"),
                  " · ".join(escape(sp.get(lang)) for sp in cl.specializations.values())]

    rows = [[btn(t(lang, "btn.classes"), cb("clsl"))]]
    if mine:
        rows[0].append(btn(t(lang, "btn.full_sheet"), cb("sheet")))
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


# ---------------------------------------------------------------- bestiary

CREATURE_ICONS = {"beast": "🐾", "undead": "💀", "humanoid": "🗡️"}  # for creatures without an icon of their own


def creature_icon(m) -> str:
    return m.icon or CREATURE_ICONS.get(m.type, "•")


def bestiary_list(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    known = bestiary.known(char)
    lines = [t(lang, "bestiary.title", seen=len(known), total=len(c.monsters)), ""]
    rows = []
    for key, entry in known:
        m = c.monsters[key]
        rows.append([btn(f"{creature_icon(m)} {m.name.get(lang)} · ⚔️ {entry.get('killed', 0)}",
                         cb("jb", key))])
    lines.append(f"<i>{t(lang, 'bestiary.hint' if known else 'bestiary.empty')}</i>")
    rows.append([btn(t(lang, "btn.back"), cb("jr"))])
    return "\n".join(lines), markup(rows)


def bestiary_entry(char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """A stat block that fills in with experience: seen, first kill, three kills."""
    c = get_content()
    back = markup([[btn(t(lang, "btn.back"), cb("jrb"))]])
    entry = (char.bestiary or {}).get(key)
    level = bestiary.tier(entry)
    if key not in c.monsters or level == 0:
        return t(lang, "bestiary.unknown"), back
    m = c.monsters[key]
    lines = [f"{creature_icon(m)} <b>{escape(m.name.get(lang))}</b>",
             f"<i>{t(lang, 'creature.' + m.type)} · {t(lang, 'bestiary.active.' + m.active)}</i>",
             RULE, escape(m.description.get(lang))]
    if m.lore:
        lines += ["", escape(m.lore.get(lang))]
    if m.habitat:
        lines += ["", t(lang, "bestiary.habitat", place=escape(m.habitat.get(lang)))]
    lines.append(t(lang, "bestiary.record", seen=entry.get("seen", 0), killed=entry.get("killed", 0)))
    if level >= 2:
        lines += ["", f"<b>{t(lang, 'bestiary.stats')}</b>",
                  t(lang, "bestiary.hp_ac", hp=m.hp, ac=m.ac)]
        for a in m.attacks:
            icon = "🏹" if a.ranged else "🗡️"
            lines.append(f"{icon} {escape(a.name.get(lang))}: {a.to_hit:+d} · {a.damage} "
                         f"{escape(t(lang, 'dmg.' + a.damage_type))}")
    else:
        lines += ["", f"🔒 <i>{t(lang, 'bestiary.locked_stats')}</i>"]
    if level >= 3:
        lines += ["", f"<b>{t(lang, 'bestiary.secrets')}</b>"]
        for field, label in (("vulnerable", "bestiary.vulnerable"), ("resist", "bestiary.resist"),
                             ("immune_damage", "bestiary.immune")):
            values = getattr(m, field)
            if values:
                lines.append(t(lang, label, list=", ".join(t(lang, "dmg." + v) for v in values)))
        if m.immune:
            lines.append(t(lang, "bestiary.immune_status", list=", ".join(t(lang, "status." + s) for s in m.immune)))
        lines.append(t(lang, "bestiary.xp", xp=m.xp))
        loot = [c.items[l.item].name.get(lang) for l in m.loot]
        if loot:
            lines.append(t(lang, "bestiary.loot", list=escape(", ".join(loot))))
    elif level == 2:
        lines += ["", f"🔒 <i>{t(lang, 'bestiary.locked_secrets', n=bestiary.KILLS_FOR_SECRETS)}</i>"]
    if c.media.monster_images(key):
        back = markup([[btn(t(lang, "btn.creature_art"), cb("jbi", key)), btn(t(lang, "btn.back"), cb("jrb"))]])
    return "\n".join(lines)[:MAX_MESSAGE], back


def creature_caption(key: str, lang: str) -> str:
    m = get_content().monsters[key]
    return f"{creature_icon(m)} <b>{escape(m.name.get(lang))}</b>"


async def rumors(session: AsyncSession, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    lines = [f"<b>{t(lang, 'journal.rumors')}</b>", ""]
    found = await npcs.recent_rumors(session, limit=8)
    lines += [f"• <i>{escape(r.get(lang, r.get('en', '')))}</i>" for r in found] or [f"<i>{t(lang, 'journal.no_rumors')}</i>"]
    return "\n".join(lines)[:MAX_MESSAGE], markup([[btn(t(lang, "btn.back"), cb("jr"))]])


# ---------------------------------------------------------------- combat

def combat_powers(state: EncounterState, me, defs: dict, lang: str) -> list[tuple[str, str]]:
    """Class powers usable right now: actions (✨) while the action is free, then bonus actions (⚡)."""
    out = []
    if not me.action_used:
        for key, uses in me.abilities.items():
            a = defs.get(key)
            if a is None or a.action != "action" or (uses is not None and uses <= 0):
                continue
            out.append((key, f"✨ {a.name.get(lang)}" + (f" ({uses})" if uses is not None else "")))
    for key in available_bonus_actions(state, me, defs):
        uses = me.abilities.get(key)
        out.append((key, f"⚡ {defs[key].name.get(lang)}" + (f" ({uses})" if uses is not None else "")))
    return out


def combat_token(version: int | None, turn_index: int) -> str:
    """Third field of every combat button: "<encounter.version>.<turn_index>.<nonce>"."""
    return f"{version or 0}.{turn_index}.{nonce()}"


PANEL_BLOCKS = 6  # recent actions shown under the combatants
# results that belong to the action above them (damage of a hit, saves of a spell...): drawn indented under it
FOLLOW_UPS = {"combat.damage", "combat.absorbed", "combat.defeated", "combat.relentless", "combat.wake",
              "combat.status", "combat.immune", "combat.save", "combat.temp_hp"}


def combat_blocks(state: EncounterState, entries: list, lang: str, with_end: bool = True) -> list[list[str]]:
    """Log entries as readable blocks: an action line with its results indented below, rounds as separators."""
    blocks: list[list[str]] = []
    for e in entries:
        if not with_end and e.key.startswith("combat.end."):
            continue
        text = escape(render_event(combat_service.log_event(state, e), lang))
        if e.key == "combat.round":
            blocks.append([f"<i>{t(lang, 'combat.round_zero') if e.params.get('round') == 0 else text}</i>"])
        elif e.key in FOLLOW_UPS and blocks and not blocks[-1][0].startswith("<i>"):
            blocks[-1].append(f"   └ {text}")
        else:
            blocks.append([f"<b>{text}</b>" if e.key == "combat.crit" else text])
    return blocks


REPORT_ICON = {"victory": "🏆", "defeat": "💀", "fled": "🏃"}


def report_page(report: "combat_service.BattleReport | None", page: int, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Battle report: page 0 is the summary, then one page per round."""
    back = [btn(t(lang, "btn.continue"), cb("scene"))]
    if report is None:
        return t(lang, "report.none"), markup([back])
    c = get_content()
    pages = len(report.rounds)
    page = max(0, min(page, pages))
    place = c.locations[report.location].name.get(lang) if report.location in c.locations else report.location
    lines = [t(lang, "report.title", place=escape(place))]
    if page == 0:
        s = report.stats
        lines += [f"{REPORT_ICON.get(report.status, '⚔️')} <b>{t(lang, 'report.result.' + report.status)}</b> · "
                  + t(lang, "report.rounds", n=report.state.round), RULE,
                  t(lang, "report.dealt", dealt=s["dealt"], hits=s["hits"], attacks=s["attacks"], crits=s["crits"]),
                  t(lang, "report.received", received=s["received"], hits=s["enemy_hits"], attacks=s["enemy_attacks"])]
        if s["healed"]:
            lines.append(t(lang, "report.healed", amount=s["healed"]))
        if s["defeated"]:
            names = ", ".join((c.monsters[k].name.get(lang) if k in c.monsters else k) + (f" ×{n}" if n > 1 else "")
                              for k, n in s["defeated"].items())
            lines.append(t(lang, "report.defeated", list=escape(names)))
        shown = [ev for ev in report.rewards if ev.key not in ("progress.asi", "progress.specialization_soon")]
        if shown:
            lines += [RULE, *(f"• {escape(render_event(ev, lang))}" for ev in shown)]
        if pages:
            lines += ["", f"<i>{t(lang, 'report.hint')}</i>"]
    else:
        number, entries = report.rounds[page - 1]
        lines += [f"<b>{t(lang, 'report.round', n=number, page=page, pages=pages)}</b>", RULE,
                  *(line for block in combat_blocks(report.state, entries, lang) for line in block)]

    def go(p: int) -> str:
        return cb("rep", f"{report.encounter_id}:{p}")
    def round_of(p: int) -> int:  # page p shows report.rounds[p - 1]; round 0 is the initiative
        return report.rounds[p - 1][0]
    nav = []
    if page > 0:
        nav.append(btn(t(lang, "btn.round_prev", n=round_of(page - 1)) if page > 1 else t(lang, "btn.summary"),
                       go(page - 1)))
    if page < pages:
        nav.append(btn(t(lang, "btn.round_next", n=round_of(page + 1)), go(page + 1)))
    rows = [nav] if nav else []
    if page > 1:
        rows.append([btn(t(lang, "btn.summary"), go(0))])
    if pages:
        rows.append([btn(t(lang, "btn.full_report"), cb("repf", str(report.encounter_id)))])
    rows.append(back)
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def full_report(report: "combat_service.BattleReport | None", lang: str) -> list[str]:
    """The whole battle, round after round and blow by blow, in as many messages as it needs."""
    if report is None:
        return [t(lang, "report.none")]
    c = get_content()
    place = c.locations[report.location].name.get(lang) if report.location in c.locations else report.location
    messages, lines = [], [t(lang, "report.full_title", place=escape(place)), RULE]
    for number, entries in report.rounds:
        title = t(lang, "combat.round_zero") if number == 0 else t(lang, "combat.round", round=number)
        block = [f"<b>{title}</b>", *(line for b in combat_blocks(report.state, entries, lang) for line in b
                                      if not line.startswith("<i>")), ""]
        if sum(len(x) + 1 for x in lines + block) > MAX_MESSAGE:
            messages.append("\n".join(lines).rstrip())
            lines = []
        lines += block
    messages.append("\n".join(lines).rstrip())  # the log already ends with "🏆 Victory!"
    return [m[:MAX_MESSAGE] for m in messages]


def combat_panel(char: Character, enc_state: dict, lang: str, target_menu: str | None = None,
                 version: int | None = None) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    state = EncounterState.model_validate(enc_state)
    lines = [t(lang, "combat.panel_title", round=state.round), RULE]
    for cid in state.order:
        cb_ = state.combatants[cid]
        icon = "🔵" if cb_.side == "player" else "🔴"
        if cb_.defeated:
            lines.append(f"💀 <s>{escape(cb_.name[lang])}</s>")
            continue
        if cb_.fled:
            lines.append(f"🏃 <s>{escape(cb_.name[lang])}</s>")
            continue
        row = t(lang, f"row.{cb_.row}")
        st = " ".join(t(lang, f"status.icon.{s}") for s in cb_.statuses)
        temp = f" (+{cb_.temp_hp})" if cb_.temp_hp else ""
        lines.append(f"{icon} <b>{escape(cb_.name[lang])}</b> ❤️ {cb_.hp}/{cb_.max_hp}{temp} "
                     f"{hp_bar(cb_.hp, cb_.max_hp)} 🛡️ {cb_.ac} · {row} {st}".rstrip())
    blocks = combat_blocks(state, state.log, lang, with_end=False)[-PANEL_BLOCKS:]
    if blocks:
        lines += [RULE, *(line for block in blocks for line in block)]

    rows: list = []
    if state.status != "active":
        lines += [RULE, f"<b>{t(lang, 'combat.end.' + state.status)}</b>"]
        beasts = characters.pending_skin(char) if state.status == "victory" else []
        if beasts:
            rows.append([btn(t(lang, "btn.skin", seconds=activities.skin_seconds(beasts)),
                             cb("act", "skin:skinning", nonce()))])
        rows.append([btn(t(lang, "btn.summary_report"), cb("rep")), btn(t(lang, "btn.full_report"), cb("repf"))])
        rows.append([btn(t(lang, "btn.continue"), cb("scene"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    me = state.combatants["p1"]
    lines += [RULE, f"<b>{t(lang, 'combat.your_turn')}</b>"]
    n = combat_token(version, state.turn_index)
    defs = combat_service.ability_defs(char)

    if target_menu == "items":  # the scrolls and bombs you carry
        lines[-1] = t(lang, "combat.items_title")
        for key, qty in me.consumables.items():
            item = c.items.get(key)
            if qty > 0 and item is not None and item.combat is not None:
                rows.append([btn(f"{item.name.get(lang)} ×{qty}", cb("cb", f"itm:{key}", n))])
        rows.append([btn(t(lang, "btn.back"), cb("cbp"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    if target_menu and target_menu != "powers":
        kind, _, arg = target_menu.partition(":")
        spell = kind == "abl" and arg in defs and defs[arg].kind in ("spell", "save", "curse")
        ranged = any(a.key == arg and a.ranged for a in me.attacks) or kind in ("obj", "itm") or spell
        for foe in valid_targets(state, me, ranged):
            rows.append([btn(f"🎯 {foe.name[lang]} ({foe.hp}/{foe.max_hp})", cb("cb", f"{target_menu}:{foe.id}", n))])
        rows.append([btn(t(lang, "btn.back"), cb("cbp"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    powers = combat_powers(state, me, defs, lang)  # [(key, label)], action abilities then bonus ones
    featured = next((p for k in c.classes[char.class_key].signature for p in powers if p[0] == k), None)
    if target_menu == "powers":  # "✨ Actions": every other power you can use now
        lines[-1] = t(lang, "combat.powers_title")
        rows += [[btn(label, cb("cb", f"abl:{key}", n))] for key, label in powers if (key, label) != featured]
        rows.append([btn(t(lang, "btn.back"), cb("cbp"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    top = []
    if not me.action_used:
        top = [btn(f"⚔️ {a.name[lang]}", cb("cb", f"atk:{a.key}", n)) for a in me.attacks]
    if featured:
        top.append(btn(f"🌟 {featured[1].split(' ', 1)[1]}", cb("cb", f"abl:{featured[0]}", n)))
    rows += grid(top)
    buttons = []
    if any(p != featured for p in powers):
        buttons.append(btn(t(lang, "btn.powers"), cb("cb", "pwrs", n)))
    if not me.action_used:
        buttons.append(btn(t(lang, "btn.defend"), cb("cb", "def", n)))
        if me.consumables.get("healing_potion", 0) > 0:
            buttons.append(btn(t(lang, "btn.potion"), cb("cb", "pot", n)))
        if any(q > 0 and c.items.get(k) is not None and c.items[k].combat is not None
               for k, q in me.consumables.items()):
            buttons.append(btn(t(lang, "btn.items"), cb("cb", "itms", n)))
        for okey in state.scene_objects:
            obj = c.locations[state.location].scene_objects.get(okey)
            if obj:
                buttons.append(btn(f"🪝 {obj.name.get(lang)}", cb("cb", f"obj:{okey}", n)))
    if not me.moved:
        buttons.append(btn(t(lang, "btn.move_" + ("back" if me.row == "front" else "front")), cb("cb", "mov", n)))
    if not me.action_used:
        buttons.append(btn(t(lang, "btn.flee"), cb("cb", "flee", n)))
    buttons.append(btn(t(lang, "btn.end_turn"), cb("cb", "end", n)))
    rows += grid(buttons)
    lines.append(f"<i>{t(lang, 'combat.hint')}</i>")
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)
