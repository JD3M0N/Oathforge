"""Message text + keyboards. HTML parse mode; every dynamic string is escaped."""

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine.checks import modifier, proficiency_bonus
from oathforge.engine.combat import EncounterState, available_bonus_actions, valid_targets
from oathforge.engine.progression import skill_rank, xp_to_next
from oathforge.i18n import t
from oathforge.services import characters, combat_service, exploration, inventory, npcs, quests
from oathforge.services.events import Outcome, render_event

MAX_MESSAGE = 4000


def hp_bar(hp: int, max_hp: int, width: int = 8) -> str:
    filled = round(width * hp / max_hp) if max_hp else 0
    return "▰" * filled + "▱" * (width - filled)


def outcome_text(outcome: Outcome, lang: str, narration: str | None = None) -> str:
    parts: list[str] = []
    if narration:
        parts.append(f"<i>{escape(narration)}</i>")
    for ev in outcome.events:
        line = escape(render_event(ev, lang))
        parts.append(line if ev.key == "text" else f"• {line}")
    return "\n\n".join(p for p in parts if p)[:MAX_MESSAGE]


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
    if loc.rest_cost is not None:
        buttons.append(btn(t(lang, "btn.rest", cost=loc.rest_cost), cb("rest", "-", n)))
    rows = grid(buttons)
    for a in await quests.available_actions(session, char, present):
        if a.action.npc is None:
            rows.append([btn(a.action.label.get(lang), cb("qa", a.ref, n))])
    rows.append([btn(t(lang, "btn.inventory"), cb("inv")), btn(t(lang, "btn.sheet"), cb("sheet")),
                 btn(t(lang, "btn.journal"), cb("jr"))])
    return "\n".join(lines), markup(rows)


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

async def sheet(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    c = get_content()
    cls = c.classes[char.class_key]
    gear = await characters.equipped(session, char)
    skills = await characters.skills_of(session, char)
    nxt = xp_to_next(char.xp)
    lines = [
        f"🧙 <b>{escape(char.name)}</b>",
        t(lang, "sheet.identity", level=char.level, lineage=c.lineages[char.lineage].name.get(lang),
          cls=cls.name.get(lang), background=c.backgrounds[char.background].name.get(lang)),
        t(lang, "sheet.vitals", hp=char.hp, max_hp=char.max_hp, ac=characters.armor_class(char, gear),
          gold=char.gold, pb=proficiency_bonus(char.level)),
        t(lang, "sheet.xp", xp=char.xp, next=nxt if nxt is not None else "—"),
        "",
        " · ".join(f"{c.abilities[a].short.get(lang)} {char.abilities[a]} ({modifier(char.abilities[a]):+d})"
                   for a in c.abilities),
        "",
        f"<b>{t(lang, 'sheet.skills')}</b>",
    ]
    for key, row in skills.items():
        if row.proficient or row.xp:
            mark = "●" if row.proficient else "○"
            rank = f" ★{skill_rank(row.xp)}" if skill_rank(row.xp) else ""
            lines.append(f"{mark} {c.skills[key].name.get(lang)} {characters.skill_bonus(char, skills, key):+d}{rank}")
    lines += ["", f"<b>{t(lang, 'sheet.abilities')}</b>"]
    for key, a in cls.abilities.items():
        if a.level <= char.level:
            uses = char.resources.get(key)
            suffix = f" ({uses}/{a.uses})" if a.uses else ""
            lines.append(f"• {a.name.get(lang)}{suffix}: {a.description.get(lang)}")
    lines += ["", f"<b>{t(lang, 'sheet.reputation')}</b>"]
    for fac, value in (await npcs.reputations(session, char)).items():
        lines.append(f"• {c.factions[fac].name.get(lang)}: {value:+d}")
    lines += ["", f"<i>{c.lineages[char.lineage].trait_text.get(lang)}</i>"]
    return "\n".join(lines), markup([[btn(t(lang, "btn.back"), cb("scene"))]])


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


async def journal(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    lines = [t(lang, "journal.title"), ""]
    icons = {"available": "❔", "active": "📜", "completed": "✅", "failed": "❌"}
    for quest, prog in await quests.journal(session, char):
        lines.append(f"{icons.get(prog.state, '📜')} <b>{escape(quest.name.get(lang))}</b>")
        lines.append(escape(quest.stages[prog.stage].journal.get(lang)))
        lines.append("")
    rumors = await npcs.recent_rumors(session, limit=3)
    if rumors:
        lines.append(f"<b>{t(lang, 'journal.rumors')}</b>")
        lines += [f"• <i>{escape(r.get(lang, r.get('en', '')))}</i>" for r in rumors]
    return "\n".join(lines), markup([[btn(t(lang, "btn.back"), cb("scene"))]])


# ---------------------------------------------------------------- combat

def combat_panel(char: Character, enc_state: dict, lang: str, target_menu: str | None = None
                 ) -> tuple[str, InlineKeyboardMarkup]:
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
        lines.append(f"{icon} <b>{escape(cb_.name[lang])}</b> {cb_.hp}/{cb_.max_hp} {hp_bar(cb_.hp, cb_.max_hp)} "
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
    n = nonce()
    defs = combat_service.ability_defs(char)

    if target_menu:
        kind, _, arg = target_menu.partition(":")
        ranged = any(a.key == arg and a.ranged for a in me.attacks) or kind == "obj"
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
            buttons.append(btn(f"✨ {a.name.get(lang)} ({uses})", cb("cb", f"abl:{key}", n)))
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
