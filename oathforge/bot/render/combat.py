"""Combat panel, powers, help and battle reports."""

from html import escape

from telegram import InlineKeyboardMarkup

from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine import combat_help
from oathforge.engine.combat import EncounterState, affordable, available_bonus_actions, valid_targets
from oathforge.i18n import t
from oathforge.services import activities, characters, combat_service
from oathforge.services.events import render_event
from oathforge.bot.render.common import MAX_MESSAGE, REPORT_ICON, RULE, hp_bar


def combat_powers(state: EncounterState, me, defs: dict, lang: str) -> list[tuple[str, str]]:
    """Class powers usable right now: actions (✨) while the action is free, then bonus actions (⚡)."""
    out = []
    if not me.action_used:
        for key, uses in me.abilities.items():
            a = defs.get(key)
            if a is None or a.action != "action" or (uses is not None and uses <= 0):
                continue
            if not affordable(me, key, a):  # it is there, it just cannot be paid for yet
                continue
            out.append((key, f"✨ {a.name.get(lang)}{_cost_tag(me, uses, a)}"))
    for key in available_bonus_actions(state, me, defs):
        out.append((key, f"⚡ {defs[key].name.get(lang)}{_cost_tag(me, me.abilities.get(key), defs[key])}"))
    return out


def _cost_tag(me, uses: int | None, ability) -> str:
    """What the button says after the name: the uses left, or what the bar will pay."""
    if me.resource_max and ability.cost:
        return f" ({ability.cost})"
    return f" ({uses})" if uses is not None else ""


def combat_help_text(state: EncounterState, me, defs: dict, lang: str) -> str:
    """💡 A short popup: what the fight asks for now, and the hero's own abilities that answer it."""
    lines = []
    for key, roles in combat_help.hints(state, me, defs):
        names = {role: ", ".join(defs[k].name.get(lang) for k in keys[:2]) for role, keys in roles.items() if keys}
        lines.append(
            t(
                lang,
                f"chelp.{key}",
                **{role: names.get(role, t(lang, "chelp.none")) for role in ("heal", "guard", "damage", "control")},
            )
        )
    return "\n".join(lines)


def combat_token(version: int | None, turn_index: int) -> str:
    """Third field of every combat button: "<encounter.version>.<turn_index>.<nonce>"."""
    return f"{version or 0}.{turn_index}.{nonce()}"


PANEL_BLOCKS = 6  # recent actions shown under the combatants
# results that belong to the action above them (damage of a hit, saves of a spell...): drawn indented under it
FOLLOW_UPS = {
    "combat.plate_hit",
    "combat.plate_broken",
    "combat.damage",
    "combat.absorbed",
    "combat.defeated",
    "combat.relentless",
    "combat.wake",
    "combat.status",
    "combat.immune",
    "combat.save",
    "combat.temp_hp",
}


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
        lines += [
            f"{REPORT_ICON.get(report.status, '⚔️')} <b>{t(lang, 'report.result.' + report.status)}</b> · "
            + t(lang, "report.rounds", n=report.state.round),
            RULE,
            t(lang, "report.dealt", dealt=s["dealt"], hits=s["hits"], attacks=s["attacks"], crits=s["crits"]),
            t(lang, "report.received", received=s["received"], hits=s["enemy_hits"], attacks=s["enemy_attacks"]),
        ]
        if s["healed"]:
            lines.append(t(lang, "report.healed", amount=s["healed"]))
        if s["defeated"]:
            names = ", ".join(
                (c.monsters[k].name.get(lang) if k in c.monsters else k) + (f" ×{n}" if n > 1 else "")
                for k, n in s["defeated"].items()
            )
            lines.append(t(lang, "report.defeated", list=escape(names)))
        shown = [ev for ev in report.rewards if ev.key not in ("progress.path_open", "progress.choice")]
        if shown:
            lines += [RULE, *(f"• {escape(render_event(ev, lang))}" for ev in shown)]
        if pages:
            lines += ["", f"<i>{t(lang, 'report.hint')}</i>"]
    else:
        number, entries = report.rounds[page - 1]
        lines += [
            f"<b>{t(lang, 'report.round', n=number, page=page, pages=pages)}</b>",
            RULE,
            *(line for block in combat_blocks(report.state, entries, lang) for line in block),
        ]

    def go(p: int) -> str:
        return cb("rep", f"{report.encounter_id}:{p}")

    def round_of(p: int) -> int:  # page p shows report.rounds[p - 1]; round 0 is the initiative
        return report.rounds[p - 1][0]

    nav = []
    if page > 0:
        nav.append(
            btn(t(lang, "btn.round_prev", n=round_of(page - 1)) if page > 1 else t(lang, "btn.summary"), go(page - 1))
        )
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
        block = [
            f"<b>{title}</b>",
            *(line for b in combat_blocks(report.state, entries, lang) for line in b if not line.startswith("<i>")),
            "",
        ]
        if sum(len(x) + 1 for x in lines + block) > MAX_MESSAGE:
            messages.append("\n".join(lines).rstrip())
            lines = []
        lines += block
    messages.append("\n".join(lines).rstrip())  # the log already ends with "🏆 Victory!"
    return [m[:MAX_MESSAGE] for m in messages]


def combat_panel(
    char: Character, enc_state: dict, lang: str, target_menu: str | None = None, version: int | None = None
) -> tuple[str, InlineKeyboardMarkup]:
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
        if cb_.form and cb_.form in cb_.shapes:
            st = f"{cb_.shapes[cb_.form].icon} {st}".strip()
        temp = f" (+{cb_.temp_hp})" if cb_.temp_hp else ""
        lines.append(
            f"{icon} <b>{escape(cb_.name[lang])}</b> ❤️ {cb_.hp}/{cb_.max_hp}{temp} "
            f"{hp_bar(cb_.hp, cb_.max_hp)} 🛡️ {cb_.ac} · {row} {st}".rstrip()
        )
        if cb_.plate_max:  # the boss's protection and what it is about to do
            lines.append(
                "   "
                + (
                    t(
                        lang,
                        "combat.plate_line",
                        plate=cb_.plate,
                        max=cb_.plate_max,
                        bar=hp_bar(cb_.plate, cb_.plate_max),
                    )
                    if cb_.plate
                    else t(lang, "combat.plate_gone")
                )
            )
        if cb_.pattern_state != "ready":
            lines.append("   " + t(lang, f"combat.intent_{cb_.pattern_state}"))
        if cb_.resource_max:  # one main bar, and nothing else in the header (roadmap_balance N15)
            res = c.progression.resources[cb_.resource_key]
            lines.append(
                f"   🔹 {escape(res.name.get(lang))} {cb_.resource}/{cb_.resource_max} "
                f"{hp_bar(cb_.resource, cb_.resource_max)}"
            )
        for ent in (e for e in state.entities.values() if e.owner == cid):  # one line per helper, no more
            name = escape(ent.name[lang])
            if ent.defeated:
                lines.append(f"   💀 <s>{ent.icon} {name}</s>")
                continue
            tag = f" ⚡{ent.boost}" if ent.boost else ""
            lines.append(f"   {ent.icon} <b>{name}</b> ❤️ {ent.hp}/{ent.max_hp}{tag}")
    blocks = combat_blocks(state, state.log, lang, with_end=False)[-PANEL_BLOCKS:]
    if blocks:
        lines += [RULE, *(line for block in blocks for line in block)]

    rows: list = []
    if state.status != "active":
        lines += [RULE, f"<b>{t(lang, 'combat.end.' + state.status)}</b>"]
        beasts = characters.pending_skin(char) if state.status == "victory" else []
        if beasts:
            rows.append(
                [btn(t(lang, "btn.skin", seconds=activities.skin_seconds(beasts)), cb("act", "skin:skinning", nonce()))]
            )
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
                rows.append([btn(f"{item.label(lang)} ×{qty}", cb("cb", f"itm:{key}", n))])
        rows.append([btn(t(lang, "btn.back"), cb("cbp"))])
        return "\n".join(lines)[:MAX_MESSAGE], markup(rows)

    if target_menu and target_menu != "powers":
        kind, _, arg = target_menu.partition(":")
        spell = (
            kind == "abl"
            and arg in defs
            and (
                defs[arg].kind in ("spell", "save", "curse", "command")
                or (defs[arg].kind == "strike" and defs[arg].ranged)
            )
        )
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
        if any(
            q > 0 and c.items.get(k) is not None and c.items[k].combat is not None for k, q in me.consumables.items()
        ):
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
    buttons.append(btn(t(lang, "btn.help"), cb("cb", "hlp", n)))
    rows += grid(buttons)
    lines.append(f"<i>{t(lang, 'combat.hint')}</i>")
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)
