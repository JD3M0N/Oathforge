"""Message text + keyboards. HTML parse mode; every dynamic string is escaped."""

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.ai.client import usage_today
from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine.checks import modifier, proficiency_bonus
from oathforge.engine.combat import EncounterState, available_bonus_actions, valid_targets
from oathforge.engine.progression import MAX_LEVEL, XP_THRESHOLDS, skill_rank
from oathforge.i18n import t
from oathforge.services import bestiary, characters, combat_service, exploration, inventory, npcs, quests
from oathforge.services.events import Outcome, render_event

MAX_MESSAGE = 4000


def hp_bar(hp: int, max_hp: int, width: int = 8) -> str:
    filled = round(width * hp / max_hp) if max_hp else 0
    return "▰" * filled + "▱" * (width - filled)


# level-up events leave the bullet list and get a card of their own (level_up_cards)
LEVEL_KEYS = {"progress.level_up", "progress.new_ability", "progress.asi", "progress.specialization_soon"}
ABILITY_ICON = {"strike": "⚔️", "spell": "🔮", "turn": "☀️", "buff": "🎶", "surge": "💢", "heal": "💚",
                "hide": "🥷", "save": "🌀", "curse": "🕯️", "passive": "🌟"}


def outcome_text(outcome: Outcome, lang: str, narration: str | None = None) -> str:
    parts: list[str] = []
    if narration:
        parts.append(f"<i>{escape(narration)}</i>")
    for ev in outcome.events:
        if ev.key in LEVEL_KEYS:
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


def ability_block(a, lang: str, prefix: str = "") -> list[str]:
    """Name, tags and description of a class ability, as in the level-up card and /class_<key>."""
    icon = ABILITY_ICON.get(a.kind, "✨")
    return [f"{prefix}{icon} <b>{escape(a.name.get(lang))}</b> · {ability_tags(a, lang)}",
            f"      <i>{escape(a.description.get(lang))}</i>"]


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
                    lines += ["", t(lang, "level_card.new"), *ability_block(a, lang)]
        if cls_key:
            lines += ["", t(lang, "level_card.class", cmd=f"/class_{cls_key}")]
        cards.append("\n".join(lines)[:MAX_MESSAGE])
        pending = []
    return cards


def status_line(char: Character, lang: str) -> str:
    night = exploration.is_night()
    tod = t(lang, "scene.night" if night else "scene.day")
    injured = " · " + t(lang, "sheet.injured") if char.conditions.get("injured") else ""
    return t(lang, "scene.status", time=tod, hp=char.hp, max_hp=char.max_hp, gold=char.gold) + injured


# ---------------------------------------------------------------- scene

async def scene(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
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
        names = ", ".join(f"{c.npcs[k].name.get(lang)} ({c.npcs[k].title.get(lang)})" for k in present)
        lines += ["", t(lang, "scene.people", names=escape(names))]
    lines += ["", f"<i>{t(lang, 'scene.hint')}</i>"]

    n = nonce()
    buttons = [btn(t(lang, "btn.travel"), cb("trv")), btn(t(lang, "btn.investigate"), cb("look", "-", n))]
    if present:
        buttons.append(btn(t(lang, "btn.talk"), cb("talkm")))
    if any(c.npcs[k].shop for k in present):
        buttons.append(btn(t(lang, "btn.shop"), cb("shopm")))
    if loc.hunting:
        buttons.append(btn(t(lang, "btn.hunt_night" if night and loc.night_encounters else "btn.hunt"),
                           cb("hunt", "-", n)))
    if loc.rest_cost is not None:
        buttons.append(btn(t(lang, "btn.rest", cost=loc.rest_cost), cb("rest", "-", n)))
    if loc.hub and c.media.zone_images(loc.zone, night):
        buttons.append(btn(t(lang, "btn.view_city"), cb("city")))
    rows = grid(buttons)
    for a in await quests.available_actions(session, char, present):
        if a.action.npc is None:
            rows.append([btn(a.action.label.get(lang), cb("qa", a.ref, n))])
    rows.append([btn(t(lang, "btn.inventory"), cb("inv")), btn(t(lang, "btn.sheet"), cb("hero")),
                 btn(t(lang, "btn.journal"), cb("jr"))])
    return "\n".join(lines), markup(rows)


def zone_caption(zone_key: str, lang: str) -> str:
    """Caption for the zone's images ("View city"): name and day/night description."""
    zone = get_content().zones[zone_key]
    desc = zone.night if exploration.is_night() and zone.night else zone.description
    return f"🏙️ <b>{escape(zone.name.get(lang))}</b>\n\n{escape(desc.get(lang))}"


def travel_menu(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    n = nonce()
    rows = []
    for e in exploration.exits(char):
        danger = "⚠️" * e.danger
        rows.append([btn(f"🧭 {c.locations[e.to].name.get(lang)} · {e.minutes} min {danger}".strip(),
                         cb("go", e.to, n))])
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return t(lang, "travel.title"), markup(rows)


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
    text.append(escape(line) if line else escape(npc.greeting.get(lang)))
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


async def shop(session: AsyncSession, char: Character, npc_key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    npc = c.npcs[npc_key]
    rep = await npcs.reputation_with(session, char, npc.faction)
    n = nonce()
    lines = [t(lang, "shop.title", npc=escape(npc.name.get(lang)), gold=char.gold)]
    rows = []
    for key in npc.shop.items:
        price = inventory.buy_price(key, rep)
        rows.append([btn(f"{c.items[key].name.get(lang)} · {price} 🪙", cb("buy", f"{npc_key}:{key}", n))])
    if npc.shop.buys:
        rows.append([btn(t(lang, "btn.sell"), cb("sellm", npc_key))])
    rows.append([btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines), markup(rows)


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
        f"{escape(c.backgrounds[char.background].name.get(lang))}</i>",
        RULE,
        t(lang, "sheet.hp", hp=char.hp, max_hp=char.max_hp, bar=hp_bar(char.hp, char.max_hp)),
    ]
    if char.level < MAX_LEVEL:
        lo, hi = XP_THRESHOLDS[char.level - 1], XP_THRESHOLDS[char.level]
        lines.append(t(lang, "sheet.xp", xp=char.xp, next=hi, bar=hp_bar(char.xp - lo, hi - lo)))
    else:
        lines.append(t(lang, "sheet.xp_max", xp=char.xp))
    lines.append(t(lang, "sheet.vitals", ac=characters.armor_class(char, gear), pb=proficiency_bonus(char.level),
                   gold=char.gold))
    if char.conditions.get("injured"):
        lines.append(t(lang, "sheet.injured"))
    return lines


def _sheet_attributes(c, cls, char: Character, lang: str) -> list[str]:
    """Ability scores, two per row in a monospace block; ★ marks the class's primary."""
    cells = []
    for a in c.abilities:
        star = "★" if a == cls.primary else " "
        score = char.abilities[a]
        cells.append(f"{c.abilities[a].short.get(lang):<3} {score:>2} ({modifier(score):+d}){star}")
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
            lines.append(f"✨ <b>{escape(a.name.get(lang))}</b>{_uses(char, key, a)}: {escape(a.description.get(lang))}")
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
              f"📖 <i>{escape(c.backgrounds[char.background].description.get(lang))}</i>"]

    # today's AI budget
    limit = get_settings().ai_user_daily_calls
    calls, _ = await usage_today(session, char.user_id)
    left = max(0, limit - calls)
    lines += [RULE, t(lang, "sheet.ai_usage", calls=calls, limit=limit, left=left, bar=hp_bar(left, limit))]

    kb = markup([[btn(t(lang, "btn.hero_summary"), cb("hero"))],
                 [btn(t(lang, "btn.inventory"), cb("inv")), btn(t(lang, "btn.journal"), cb("jr"))],
                 [btn(t(lang, "btn.back"), cb("scene"))]])
    return "\n".join(lines)[:MAX_MESSAGE], kb


async def inventory_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    n = nonce()
    lines = [t(lang, "inv.title", gold=char.gold), ""]
    rows = []
    for inst in await inventory.items_of(session, char):
        item = c.items[inst.item_key]
        qty = f" ×{inst.qty}" if inst.qty > 1 else ""
        worn = " ✅" if inst.equipped_slot else ""
        lines.append(f"• {escape(item.name.get(lang))}{qty}{worn}: <i>{escape(item.description.get(lang))}</i>")
        if item.slot:
            label = t(lang, "btn.unequip" if inst.equipped_slot else "btn.equip", item=item.name.get(lang))
            rows.append([btn(label, cb("eq", str(inst.id), n))])
        elif item.heal:
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
    kb = markup([[btn(t(lang, "btn.missions"), cb("jrm")), btn(t(lang, "btn.bestiary"), cb("jrb"))],
                 [btn(t(lang, "btn.rumors"), cb("jrr")), btn(t(lang, "btn.back"), cb("scene"))]])
    return "\n".join(lines)[:MAX_MESSAGE], kb


async def missions(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    entries = await quests.journal(session, char)
    done = sum(1 for _, q, p in entries if quests.stage_of(q, p)[1] == "completed")
    lines = [t(lang, "journal.missions_title", done=done, total=len(entries)), ""]
    rows = []
    for key, quest, prog in entries:
        _, state = quests.stage_of(quest, prog)
        name = quest.name.get(lang) if state != "locked" else t(lang, "journal.locked_name")
        rows.append([btn(f"{QUEST_ICONS[state]} {name}", cb("jq", key))])
    lines.append(f"<i>{t(lang, 'journal.missions_hint')}</i>")
    rows.append([btn(t(lang, "btn.back"), cb("jr"))])
    return "\n".join(lines), markup(rows)


async def mission(session: AsyncSession, char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    back = markup([[btn(t(lang, "btn.back"), cb("jrm"))]])
    entry = next(((q, p) for k, q, p in await quests.journal(session, char) if k == key), None)
    if entry is None:
        return t(lang, "quest.err.unavailable"), back
    quest, prog = entry
    stage, state = quests.stage_of(quest, prog)
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
    for a in sorted(cl.abilities.values(), key=lambda a: a.level):
        mark = ("✅ " if a.level <= char.level else "🔒 ") if mine else ""
        lines += ["", *ability_block(a, lang, prefix=f"{mark}<b>{t(lang, 'classes.level', level=a.level)}</b> · ")]
    if cl.specializations:
        lines += [RULE, t(lang, "classes.specializations"),
                  " · ".join(escape(sp.get(lang)) for sp in cl.specializations.values())]

    rows = [[btn(t(lang, "btn.classes"), cb("clsl"))]]
    if mine:
        rows[0].append(btn(t(lang, "btn.full_sheet"), cb("sheet")))
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


# ---------------------------------------------------------------- bestiary

CREATURE_ICONS = {"beast": "🐗", "undead": "💀", "humanoid": "🗡️"}


def bestiary_list(char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    known = bestiary.known(char)
    lines = [t(lang, "bestiary.title", seen=len(known), total=len(c.monsters)), ""]
    rows = []
    for key, entry in known:
        m = c.monsters[key]
        rows.append([btn(f"{CREATURE_ICONS.get(m.type, '•')} {m.name.get(lang)} · ⚔️ {entry.get('killed', 0)}",
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
    lines = [f"{CREATURE_ICONS.get(m.type, '•')} <b>{escape(m.name.get(lang))}</b>",
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
    return "\n".join(lines)[:MAX_MESSAGE], back


async def rumors(session: AsyncSession, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    lines = [f"<b>{t(lang, 'journal.rumors')}</b>", ""]
    found = await npcs.recent_rumors(session, limit=8)
    lines += [f"• <i>{escape(r.get(lang, r.get('en', '')))}</i>" for r in found] or [f"<i>{t(lang, 'journal.no_rumors')}</i>"]
    return "\n".join(lines)[:MAX_MESSAGE], markup([[btn(t(lang, "btn.back"), cb("jr"))]])


# ---------------------------------------------------------------- combat

def combat_token(version: int | None, turn_index: int) -> str:
    """Third field of every combat button: "<encounter.version>.<turn_index>.<nonce>"."""
    return f"{version or 0}.{turn_index}.{nonce()}"


def combat_panel(char: Character, enc_state: dict, lang: str, target_menu: str | None = None,
                 version: int | None = None) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    state = EncounterState.model_validate(enc_state)
    lines = [t(lang, "combat.panel_title", round=state.round), ""]
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
        lines.append(f"{icon} <b>{escape(cb_.name[lang])}</b> {cb_.hp}/{cb_.max_hp}{temp} {hp_bar(cb_.hp, cb_.max_hp)} "
                     f"· {row} {st}".rstrip())
    recent = state.log[-7:]
    if recent:
        lines += ["", *(f"› {escape(render_event(combat_service.log_event(state, e), lang))}" for e in recent)]

    rows: list = []
    if state.status != "active":
        lines += ["", f"<b>{t(lang, 'combat.end.' + state.status)}</b>"]
        rows.append([btn(t(lang, "btn.continue"), cb("scene"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    me = state.combatants["p1"]
    lines += ["", f"<b>{t(lang, 'combat.your_turn')}</b>"]
    n = combat_token(version, state.turn_index)
    defs = combat_service.ability_defs(char)

    if target_menu:
        kind, _, arg = target_menu.partition(":")
        spell = kind == "abl" and arg in defs and defs[arg].kind in ("spell", "save", "curse")
        ranged = any(a.key == arg and a.ranged for a in me.attacks) or kind == "obj" or spell
        for foe in valid_targets(state, me, ranged):
            rows.append([btn(f"🎯 {foe.name[lang]} ({foe.hp}/{foe.max_hp})", cb("cb", f"{target_menu}:{foe.id}", n))])
        rows.append([btn(t(lang, "btn.back"), cb("cbp"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    buttons = []
    if not me.action_used:
        for a in me.attacks:
            buttons.append(btn(f"⚔️ {a.name[lang]}", cb("cb", f"atk:{a.key}", n)))
        for key, uses in me.abilities.items():
            a = defs.get(key)
            if a is None or a.action != "action" or (uses is not None and uses <= 0):
                continue
            label = f"✨ {a.name.get(lang)}" + (f" ({uses})" if uses is not None else "")
            buttons.append(btn(label, cb("cb", f"abl:{key}", n)))
    for key in available_bonus_actions(state, me, defs):
        uses = me.abilities.get(key)
        label = f"⚡ {defs[key].name.get(lang)}" + (f" ({uses})" if uses is not None else "")
        buttons.append(btn(label, cb("cb", f"abl:{key}", n)))
    if not me.action_used:
        buttons.append(btn(t(lang, "btn.defend"), cb("cb", "def", n)))
        buttons.append(btn(t(lang, "btn.potion"), cb("cb", "pot", n)))
        for okey in state.scene_objects:
            obj = c.locations[state.location].scene_objects.get(okey)
            if obj:
                buttons.append(btn(f"🪝 {obj.name.get(lang)}", cb("cb", f"obj:{okey}", n)))
    if not me.moved:
        buttons.append(btn(t(lang, "btn.move_" + ("back" if me.row == "front" else "front")), cb("cb", "mov", n)))
    if not me.action_used:
        buttons.append(btn(t(lang, "btn.flee"), cb("cb", "flee", n)))
    buttons.append(btn(t(lang, "btn.end_turn"), cb("cb", "end", n)))
    rows = grid(buttons)
    lines.append(f"<i>{t(lang, 'combat.hint')}</i>")
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)
