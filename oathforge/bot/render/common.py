"""Shared pieces: message size, HP bar, icons, item stats, journal tabs and the rulebook numbers."""

import re
from html import escape

from oathforge.bot.keyboards import btn, cb, grid
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.content.schemas import DC_TIERS
from oathforge.database.models import Character
from oathforge.engine import combat, gathering, pointbuy, timings
from oathforge.i18n import t
from oathforge.services import activities, characters, exploration, professions, specializations, world_map
from oathforge.services.events import Outcome, render_event

MAX_MESSAGE = 4000


def hp_bar(hp: int, max_hp: int, width: int = 8) -> str:
    filled = round(width * hp / max_hp) if max_hp else 0
    return "▰" * filled + "▱" * (width - filled)


# level-up events leave the bullet list and get a card of their own (level_up_cards)
LEVEL_KEYS = {"progress.level_up", "progress.new_ability", "progress.path_open", "progress.choice"}
ABILITY_ICON = {
    "strike": "⚔️",
    "spell": "🔮",
    "turn": "☀️",
    "buff": "🎶",
    "surge": "💢",
    "heal": "💚",
    "hide": "🥷",
    "save": "🌀",
    "curse": "🕯️",
    "passive": "🌟",
}


def panel_only(key: str) -> bool:
    """Blow-by-blow combat logs: the combat panel (sent right after) already shows them."""
    return (
        key.startswith("combat.")
        and key not in ("combat.start", "combat.defeat_penalty", "combat.defeat_penalty_free")
        and not key.startswith("combat.err.")
    )


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


def status_line(char: Character, lang: str) -> str:
    night = exploration.is_night()
    tod = t(
        lang, "scene.night" if night else "scene.day", clock=exploration.clock(), minutes=exploration.until_switch()
    )
    injured = " · " + t(lang, "sheet.injured") if char.conditions.get("injured") else ""
    return t(lang, "scene.status", time=tod, hp=char.hp, max_hp=char.max_hp, gold=char.gold) + injured


SKINNING_TOOL = activities.SKINNING_KNIFE
MASTERY_ICON = {
    "mining": "⛏️",
    "woodcutting": "🪓",
    "herbalism": "🌿",
    "skinning": "🔪",
    "fishing": "🎣",
    "tracking": "🐾",
}


ACTIVITY_ICON = {**MASTERY_ICON, "rest": "🛏️"}


def discipline_icon(key: str) -> str:
    """The icon of a crafting discipline: a profession's own, or the icon of that field mastery."""
    prof = get_content().professions.get(key)
    return prof.icon if prof is not None else MASTERY_ICON.get(key, "🛠️")


def discipline_label(key: str, lang: str) -> str:
    """ "⛏️ Minería" or "⚒️ Herrería": refining belongs to a mastery, crafting to a profession."""
    prof = get_content().professions.get(key)
    name = prof.name.get(lang) if prof is not None else t(lang, f"mastery.name.{key}")
    return f"{discipline_icon(key)} {name}"


def _go_button(route: world_map.Route, lang: str, n: str, icon: str = "🧭") -> list:
    name = get_content().locations[route.to].name.get(lang)
    return [btn(f"{icon} {name} · {route.yards} yd {'⚠️' * route.danger}".strip(), cb("go", route.to, n))]


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


SLOT_ICONS = {"main_hand": "🗡️", "ranged": "🏹", "off_hand": "🛡️", "body": "🥋"}
RULE = "━━━━━━━━━━━━━━━━"


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


JOURNAL_TABS = (
    ("jr", "now"),
    ("jrm", "missions"),
    ("jrc", "chronicle"),
    ("ach", "achievements"),
    ("jrb", "bestiary"),
    ("jrr", "rumors"),
    ("jrs", "stats"),
)


def journal_tabs(active: str, lang: str) -> list[list]:
    """The same bar on every tab, the current one between dots, as the inventory does."""
    return grid(
        [
            btn(
                ("• " if verb == active else "") + t(lang, f"journal.tab.{key}") + (" •" if verb == active else ""),
                cb(verb),
            )
            for verb, key in JOURNAL_TABS
        ]
    ) + [[btn(t(lang, "btn.back"), cb("scene"))]]


RULE_NUMBER = re.compile(r"\{(\w+)\}")


def rule_numbers(lang: str = "es") -> dict:
    """{placeholders} in content/rulebook.yaml, straight from the engine, so the rulebook never goes stale."""
    c = get_content()
    ambush = [g.stay_ambush for loc in c.locations.values() for g in loc.gathering if g.stay_ambush]
    rest_costs = [loc.rest_cost for loc in c.locations.values() if loc.rest_cost]
    skins = [m.skin_seconds for m in c.monsters.values() if m.skin_seconds]
    settings = get_settings()
    return {
        "dc_trivial": DC_TIERS["trivial"],
        "dc_easy": DC_TIERS["easy"],
        "dc_medium": DC_TIERS["medium"],
        "dc_hard": DC_TIERS["hard"],
        "dc_very_hard": DC_TIERS["very_hard"],
        "max_level": len(c.progression.xp),
        "branch_level": c.progression.specialization_level,
        "training_levels": ", ".join(str(n) for n in c.progression.training_levels),
        "points": pointbuy.BUDGET,
        "flee_dc_base": combat.FLEE_DC_BASE,
        "flee_dc_step": combat.FLEE_DC_PER_FOE,
        "defeat_gold_pct": characters.DEFEAT_GOLD_PCT,
        "rest_gold": min(rest_costs) if rest_costs else 0,
        "skin_s": min(skins) if skins else 0,
        "skin_s_max": max(skins) if skins else 0,
        "trip_base": round(exploration.ENCOUNTER_CHANCE_PER_DANGER * 100),
        "trip_step": round(exploration.TRIP_EXTRA_PER_STRETCH * 100),
        "trip_cap": round(exploration.TRIP_CHANCE_CAP * 100),
        "gather_min": timings.GATHER_SECONDS // 60,
        "stay_min": timings.STAY_SECONDS // 60,
        "track_min": timings.TRACK_SECONDS // 60,
        "rest_min": timings.REST_SECONDS // 60,
        "short_rest_min": timings.SHORT_REST_SECONDS // 60,
        "short_rests": timings.SHORT_RESTS_PER_LONG,
        "short_rest_pct": round(timings.SHORT_REST_HP_PCT * 100),
        "heal_gold": min((loc.healer.cost for loc in c.locations.values() if loc.healer), default=0),
        "defeat_gold_cap": characters.DEFEAT_GOLD_CAP_PER_LEVEL,
        "gather_units": "{}–{}".format(*gathering.GATHER_UNITS),
        "stay_units": "{}–{}".format(*gathering.STAY_UNITS),
        "ambush": f"{round(min(ambush) * 100)}–{round(max(ambush) * 100)} %" if ambush else "—",
        "prey_pct": round(gathering.TRACK_PREY_CHANCE * 100),
        "bonus_pct": round(gathering.BONUS_PER_RANK * 100),
        "bonus_cap": round(gathering.BONUS_CAP * 100),
        "max_rank": gathering.MAX_RANK,
        "slots": professions.SLOTS,
        "swap_cost": professions.SWAP_COST,
        "chest_slots": settings.chest_slots,
        "chest_upgrade": settings.chest_slots_per_upgrade,
        "spec_rank": specializations.MIN_RANK,
        "spec_cost": settings.spec_switch_cost,
        "craft_batch": settings.craft_batch_max,
    }


CREATURE_ICONS = {"beast": "🐾", "undead": "💀", "humanoid": "🗡️"}  # for creatures without an icon of their own


def creature_icon(m) -> str:
    return m.icon or CREATURE_ICONS.get(m.type, "•")


REPORT_ICON = {"victory": "🏆", "defeat": "💀", "fled": "🏃"}
