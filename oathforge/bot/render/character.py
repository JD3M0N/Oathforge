"""Character sheet, abilities, level-up cards, class path, classes, lineages, backgrounds and rulebook."""

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession
from telegram import InlineKeyboardMarkup

from oathforge.ai.client import usage_today
from oathforge.bot import achievement_views
from oathforge.bot.keyboards import btn, cb, grid, markup, nonce
from oathforge.bot.render.common import (
    ABILITY_ICON,
    LEVEL_KEYS,
    MAX_MESSAGE,
    RULE,
    RULE_NUMBER,
    _gear_line,
    hp_bar,
    rule_numbers,
)
from oathforge.bot.render.crafting import hobby_lines, mastery_lines, professions_line, specializations_view
from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine.checks import modifier, proficiency_bonus
from oathforge.engine.progression import skill_rank
from oathforge.i18n import t
from oathforge.services import achievements, characters, chronicles, class_specializations, npcs, specializations
from oathforge.services.events import Outcome, render_event


def ability_tags(a, lang: str) -> str:
    """'pasiva' or 'acción adicional · 2 usos/descanso'."""
    if a.kind == "passive" or a.action == "none":
        return t(lang, "ability.passive")
    tags = [t(lang, f"ability.action.{a.action}")]
    if a.cost:  # a class with a bar pays with it
        tags.append(t(lang, "ability.cost", n=a.cost))
    else:
        tags.append(t(lang, "ability.uses", n=a.uses) if a.uses else t(lang, "ability.unlimited"))
    return " · ".join(tags)


def ability_block(a, lang: str, prefix: str = "", key: str | None = None) -> list[str]:
    """Name, tags and description of a class ability, as in the level-up card and /class_<key>."""
    icon = ABILITY_ICON.get(a.kind, "✨")
    link = f" · /skill_{key}" if key else ""
    return [
        f"{prefix}{icon} <b>{escape(a.name.get(lang))}</b> · {ability_tags(a, lang)}",
        f"      <i>{escape(a.description.get(lang))}</i>{link}",
    ]


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
        out.append(
            t(lang, "skill.heal_dice", dice=a.heal_dice) + (t(lang, f"skill.plus_{a.heal_add}") if a.heal_add else "")
        )
    if a.temp_hp:
        out.append(
            t(lang, "skill.temp_hp", dice=a.temp_hp) + (t(lang, f"skill.plus_{a.heal_add}") if a.heal_add else "")
        )
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
        out.append(
            t(
                lang,
                "skill.sneak",
                list=" · ".join(
                    t(lang, "skill.sneak_level", n=n, level=lvl) for lvl, n in sorted(a.sneak_dice.items())
                ),
            )
        )
    if a.extra_attack:
        out.append(t(lang, "skill.extra_attack"))
    if a.halve_first_hit:
        out.append(t(lang, "skill.halve_first_hit"))
    if a.crit_range:
        out.append(t(lang, "skill.crit_range", n=a.crit_range))
    if a.bonus_damage:
        out.append(t(lang, "skill.bonus_damage", dice=a.bonus_damage, type=dmg(a.bonus_damage_type)))
    if a.consumes and a.consume_damage:
        out.append(t(lang, "skill.consumes", status=t(lang, "status." + a.consumes), dice=a.consume_damage))
    if a.leech_pct:
        out.append(t(lang, "skill.leech", n=a.leech_pct))
    if a.reduces_cooldowns:
        out.append(t(lang, "skill.reduces_cooldowns", n=a.reduces_cooldowns))
    if a.thorns:
        out.append(t(lang, "skill.thorns", dice=a.thorns, type=dmg(a.bonus_damage_type or "radiant")))
    if a.resource_on_hurt:
        out.append(t(lang, "skill.resource_on_hurt", n=a.resource_on_hurt))
    if a.entity and a.entity in c.entities:
        e = c.entities[a.entity]
        out.append(t(lang, "skill.entity", icon=e.icon, name=e.name.get(lang), role=t(lang, "skill.role." + e.role)))
    if a.kind == "converge":
        out.append(t(lang, "skill.boost", turns=a.boost_turns))
    if a.form and a.form in c.forms:
        out.append(t(lang, "skill.form", icon=c.forms[a.form].icon, name=c.forms[a.form].name.get(lang)))
    elif a.form == "none":
        out.append(t(lang, "skill.form_none"))
    if a.cost:
        out.append(t(lang, "skill.cost", n=a.cost))
    if a.cooldown:
        out.append(t(lang, "skill.cooldown", n=a.cooldown))
    return [escape(line) for line in out]


def ability_owners(key: str) -> list[tuple[str, object, int, str]]:
    """Who gives an ability: (icon, name, level, class key). A class, or a branch of one."""
    c = get_content()
    owners = [
        (CLASS_ICONS.get(ck, "•"), cl.name, cl.abilities[key].level, ck)
        for ck, cl in c.classes.items()
        if key in cl.abilities
    ]
    for branch in c.class_specializations.values():
        found = branch.abilities.get(key) or next(
            (m.grants[key] for m in branch.modifiers.values() if key in m.grants), None
        )
        if found is not None:
            owners.append(("🧭", branch.name, found.level, branch.class_key))
    return owners


def skill_page(key: str, lang: str, char: Character | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """/skill_<key>: a class ability in depth (what the engine does with it). Extra Attack is in two classes."""
    owners = ability_owners(key)
    a = characters.find_ability(key)
    if not owners or a is None:
        text, kb = classes_list(lang)
        return t(lang, "skill.unknown") + "\n\n" + text, kb
    lines = [
        f"{ABILITY_ICON.get(a.kind, '✨')} <b>{escape(a.name.get(lang))}</b>",
        " · ".join(
            f"{icon} {escape(name.get(lang))} ({t(lang, 'classes.level', level=level)})"
            for icon, name, level, _ in owners
        ),
        ability_tags(a, lang),
        RULE,
        f"<i>{escape((a.details or a.description).get(lang))}</i>",
        "",
        f"<b>{t(lang, 'skill.mechanics')}</b>",
        *(f"• {line}" for line in ability_mechanics(a, lang)),
    ]
    mine = next((lvl for _, _, lvl, ck in owners if char is not None and ck == char.class_key), None)
    if mine is not None:
        lines += ["", t(lang, "skill.yours" if mine <= char.level else "skill.locked", level=mine)]
    seen, rows = set(), [[]]
    for _, _, _, ck in owners:
        if ck not in seen:
            seen.add(ck)
            rows[0].append(btn(f"{CLASS_ICONS.get(ck, '•')} {get_content().classes[ck].name.get(lang)}", cb("cls", ck)))
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def level_up_cards(outcome: Outcome, lang: str) -> list[str]:
    """One message per level gained: HP before → after, attribute boost and each new ability explained."""
    cards: list[str] = []
    pending: list = []
    for ev in outcome.events:
        if ev.key not in LEVEL_KEYS:
            continue
        if ev.key in ("progress.path_open", "progress.choice") and cards:  # they come after their level_up
            cards[-1] += "\n\n" + escape(render_event(ev, lang))
            continue
        pending.append(ev)
        if ev.key != "progress.level_up":
            continue
        p = ev.params
        lines = [
            t(lang, "level_card.title", level=p["level"]),
            RULE,
            t(
                lang,
                "level_card.hp",
                prev=p.get("prev_max_hp", p["max_hp"]),
                max_hp=p["max_hp"],
                gain=p["max_hp"] - p.get("prev_max_hp", p["max_hp"]),
            ),
        ]
        cls_key = p.get("cls")
        for e in pending:
            if e.key == "progress.new_ability":
                a = characters.find_ability(e.params.get("ability_key"))
                if a is None:
                    lines.append(escape(render_event(e, lang)))
                else:
                    lines += ["", t(lang, "level_card.new"), *ability_block(a, lang, key=e.params.get("ability_key"))]
        if cls_key:
            lines += ["", t(lang, "level_card.class", cmd=f"/class_{cls_key}")]
        cards.append("\n".join(lines)[:MAX_MESSAGE])
        pending = []
    return cards


# ---------------------------------------------------------------- the class path

ROLE_ICON = {"dmg": "⚔️", "deff": "🛡️", "heal": "💚", "control": "🌀"}


def _roles(branch, lang: str) -> str:
    return " · ".join(f"{ROLE_ICON[r]} {t(lang, 'path.role.' + r)}" for r in branch.roles)


def _branch_path_lines(branch, lang: str) -> list[str]:
    """What a branch gives, level by level, from the data and nowhere else."""
    prog = get_content().progression
    lines = []
    for a in sorted(branch.abilities.values(), key=lambda a: a.level):
        lines.append(
            f"• {t(lang, 'classes.level', level=a.level)} · {escape(a.name.get(lang))} ({ability_tags(a, lang)})"
        )
    for lvl in prog.modifier_levels:
        names = " / ".join(escape(m.name.get(lang)) for m in branch.modifiers.values() if m.level == lvl)
        if names:
            lines.append(f"• {t(lang, 'classes.level', level=lvl)} · {t(lang, 'path.modifier')}: {names}")
    return lines


async def path_view(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """🧭 Your path: the branch of your class, and the choices you owe (trainings and modifiers)."""
    c = get_content()
    prog = c.progression
    lines, rows, n = [t(lang, "path.title"), RULE], [], nonce()
    mine = c.class_specializations.get(char.specialization or "")
    if mine is not None:
        lines += [
            t(lang, "path.yours", branch=escape(mine.name.get(lang)), roles=_roles(mine, lang)),
            f"<i>{escape(mine.description.get(lang))}</i>",
        ]
        if class_specializations.reroll_available(char):
            lines += ["", t(lang, "path.reroll_hint")]
            rows += [
                [btn(f"🔁 {b.name.get(lang)}", cb("pathv", f"r:{k}", n))]
                for k, b in class_specializations.branches(char).items()
                if b.ready and k != char.specialization
            ]
    elif class_specializations.open_for(char):
        lines += [
            t(lang, "path.open", level=prog.specialization_level),
            t(lang, "path.open_where" if not c.locations[char.location].home else "path.open_here"),
            "",
        ]
        for k, b in class_specializations.branches(char).items():
            lines.append(f"{'🧭' if b.ready else '🔒'} <b>{escape(b.name.get(lang))}</b> · {_roles(b, lang)}")
            lines.append(f"<i>{escape(b.description.get(lang))}</i>")
            if b.ready:
                rows.append([btn(f"🧭 {b.name.get(lang)}", cb("pathv", f"b:{k}", n))])
        if not any(b.ready for b in class_specializations.branches(char).values()):
            lines += ["", t(lang, "path.none_ready")]
    else:
        lines.append(t(lang, "path.locked", level=prog.specialization_level, level_now=char.level))
    owed = class_specializations.pending(char)
    if owed:
        lines += ["", f"<b>{t(lang, 'path.owed')}</b>"]
        for ch in owed:
            rows.append([btn(t(lang, f"path.pick.{ch.kind}", level=ch.level), cb("pathq", ch.key, n))])
    taken = characters.taken_of(char)
    if taken:
        lines += ["", f"<b>{t(lang, 'path.taken')}</b>"]
        for key, option in sorted(taken.items(), key=lambda kv: int(kv[0].partition(":")[2] or 0)):
            kind, _, lvl = key.partition(":")
            src = prog.trainings.get(option) if kind == "training" else (mine.modifiers.get(option) if mine else None)
            if src is not None:
                lines.append(f"• {t(lang, 'classes.level', level=lvl)} · {escape(src.name.get(lang))}")
    rows.append([btn(t(lang, "btn.full_sheet"), cb("sheet")), btn(t(lang, "btn.back"), cb("scene"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def path_choice(char: Character, choice_key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The options of one pending choice, each with what it really does, before anything is final."""
    choice = next((ch for ch in class_specializations.pending(char) if ch.key == choice_key), None)
    if choice is None:
        return None
    lines = [t(lang, f"path.ask.{choice.kind}", level=choice.level), RULE]
    rows, n = [], nonce()
    for option, picked in class_specializations.options(char, choice).items():
        lines += [f"<b>{escape(picked.name.get(lang))}</b>", f"<i>{escape(picked.description.get(lang))}</i>", ""]
        rows.append([btn(picked.name.get(lang), cb("pathv", f"o:{choice_key}:{option}", n))])
    rows.append([btn(t(lang, "btn.back"), cb("path"))])
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)


def path_confirm(char: Character, arg: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The last question before a choice that cannot be undone."""
    c = get_content()
    mode, _, rest = arg.partition(":")
    n = nonce()
    if mode in ("b", "r"):
        branch = c.class_specializations.get(rest)
        if branch is None:
            return None
        lines = [
            t(
                lang,
                "path.confirm_branch" if mode == "b" else "path.confirm_reroll",
                branch=escape(branch.name.get(lang)),
            ),
            RULE,
            f"<i>{escape(branch.description.get(lang))}</i>",
            _roles(branch, lang),
            "",
            *_branch_path_lines(branch, lang),
            "",
            t(lang, "path.final"),
        ]
        go = cb("pathc", f"{mode}:{rest}", n)
    else:
        choice_key, _, option = rest.rpartition(":")
        choice = next((ch for ch in class_specializations.pending(char) if ch.key == choice_key), None)
        picked = class_specializations.options(char, choice).get(option) if choice else None
        if picked is None:
            return None
        lines = [
            t(lang, "path.confirm_pick", name=escape(picked.name.get(lang))),
            RULE,
            f"<i>{escape(picked.description.get(lang))}</i>",
            "",
            t(lang, "path.final"),
        ]
        go = cb("pathc", f"o:{choice_key}:{option}", n)
    return "\n".join(lines)[:MAX_MESSAGE], markup(
        [[btn(t(lang, "btn.confirm"), go), btn(t(lang, "btn.back"), cb("path"))]]
    )


def spec_confirm(char: Character, key: str, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """What the change costs and what gets paused, before a coin changes hands."""
    c = get_content()
    spec = c.specializations.get(key)
    if spec is None:
        return specializations_view(char, lang)
    old = specializations.active(char, spec.skill)
    cost = specializations.price(char, key)
    if not cost:  # the first branch of a discipline is free: no confirmation to collect
        return specializations_view(char, lang)
    text = t(
        lang,
        "spec.confirm",
        spec=escape(spec.name.get(lang)),
        skill=escape(characters.mastery_name(spec.skill)[lang]),
        cost=cost,
        gold=char.gold,
        old=escape(c.specializations[old].name.get(lang)),
    )
    rows = [[btn(t(lang, "btn.confirm"), cb("specc", key, nonce())), btn(t(lang, "btn.back"), cb("spec"))]]
    return text, markup(rows)


# ---------------------------------------------------------------- character sheet


def rep_label(value: int, lang: str) -> str:
    tier = (
        "hated"
        if value <= -50
        else "hostile"
        if value <= -10
        else "neutral"
        if value < 10
        else "friendly"
        if value < 50
        else "honored"
    )
    return t(lang, f"sheet.rep.{tier}")


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
    table = c.progression.xp
    if char.level < len(table):
        lo, hi = table[char.level - 1], table[char.level]
        cur = min(char.xp - lo, hi - lo)  # waiting at a gate the bar is full, never over its own total
        lines.append(
            t(lang, "sheet.xp", cur=cur, need=hi - lo, level=char.level + 1, xp=char.xp, bar=hp_bar(cur, hi - lo))
        )
    else:
        lines.append(t(lang, "sheet.xp_max", xp=char.xp))
    if gate := characters.level_gate(char):  # the XP is there; a mission is not (roadmap_balance §4.2)
        lines.append(t(lang, "sheet.level_gate", milestone=escape(c.progression.milestones[gate].name.get(lang))))
    if res := characters.resource_def(char):
        lines.append(
            t(
                lang,
                "sheet.resource",
                resource=escape(res.name.get(lang)),
                cur=characters.pool_of(char),
                max=characters.resource_max(char),
                bar=hp_bar(characters.pool_of(char), characters.resource_max(char)),
            )
        )
    lines.append(
        t(lang, "sheet.vitals", ac=characters.armor_class(char, gear), pb=proficiency_bonus(char.level), gold=char.gold)
    )
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
    pairs = ["  ".join(cells[i : i + 2]) for i in range(0, len(cells), 2)]
    return ["", f"<b>{t(lang, 'sheet.attributes')}</b>", "<code>" + escape("\n".join(pairs)) + "</code>"]


def _sheet_gear(gear: dict, lang: str) -> list[str]:
    order = ("main_hand", "ranged", "off_hand", "body")
    worn = [gear[slot] for slot in order if slot in gear]
    return [
        "",
        f"<b>{t(lang, 'sheet.gear')}</b>",
        *([_gear_line(inst, lang) for inst in worn] or [f"<i>{t(lang, 'sheet.no_gear')}</i>"]),
    ]


def _uses(char: Character, key: str, a) -> str:
    uses = char.resources.get(key)
    return f" ({a.uses if uses is None else uses}/{a.uses})" if a.uses else ""


async def hero(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Summary: vitals, attributes, gear and unlocked abilities by name. /sheet has everything."""
    ach = await achievements.snapshot(session, char)
    c = get_content()
    cls = c.classes[char.class_key]
    gear = await characters.equipped(session, char)
    lines = _sheet_top(c, cls, char, gear, lang) + _sheet_attributes(c, cls, char, lang) + _sheet_gear(gear, lang)
    lines += achievement_views.identity(ach, lang)
    unlocked = [
        escape(a.name.get(lang)) + _uses(char, key, a) for key, a in characters.effective(char).abilities.items()
    ]
    if unlocked:
        lines += ["", f"<b>{t(lang, 'sheet.abilities')}</b>", "✨ " + " · ".join(unlocked)]
    owed = len(class_specializations.pending(char)) + (1 if class_specializations.open_for(char) else 0)
    kb = markup(
        [
            [btn(t(lang, "achievements.open"), cb("ach"))],
            [btn(t(lang, "btn.path", n=owed) if owed else t(lang, "btn.path_plain"), cb("path"))],
            [btn(t(lang, "btn.full_sheet"), cb("sheet")), btn(t(lang, "btn.professions"), cb("prof"))],
            [btn(t(lang, "btn.inventory"), cb("inv")), btn(t(lang, "btn.journal"), cb("jr"))],
            [btn(t(lang, "btn.back"), cb("scene"))],
        ]
    )
    return "\n".join(lines)[:MAX_MESSAGE], kb


def portrait_caption(char: Character, lang: str) -> str:
    """Caption for the class portrait sent before the full sheet."""
    cls = get_content().classes[char.class_key]
    return (
        f"🦸 <b>{escape(char.name)}</b> · {escape(t(lang, 'sheet.identity', level=char.level, cls=cls.name.get(lang)))}"
    )


async def sheet(session: AsyncSession, char: Character, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """The full character sheet: everything the engine knows about the hero."""
    c = get_content()
    cls = c.classes[char.class_key]
    gear = await characters.equipped(session, char)
    skills = await characters.skills_of(session, char)
    lines = _sheet_top(c, cls, char, gear, lang)
    title = achievement_views.title_of(await achievements.snapshot(session, char), lang)
    extra = [f"<i>{escape(cls.description.get(lang))}</i>"]
    if title:
        extra.insert(0, f"🏅 <b>{escape(title)}</b>")
    if char.specialization in c.class_specializations:
        extra.insert(
            0, t(lang, "sheet.specialization", name=escape(c.class_specializations[char.specialization].name.get(lang)))
        )
    lines[2:2] = extra
    lines.append(t(lang, "sheet.hit_die", die=cls.hit_die))
    lines.append(t(lang, "sheet.class_link", cmd=f"/class_{char.class_key}"))
    lines += _sheet_attributes(c, cls, char, lang)

    # combat numbers: attacks, spellcasting, passive perception, immunities
    lines += ["", f"<b>{t(lang, 'sheet.combat')}</b>"]
    for a in characters.attack_profiles(char, gear):
        lines.append(
            ("🏹 " if a.ranged else "🗡️ ")
            + escape(
                t(
                    lang,
                    "sheet.attack",
                    name=a.name[lang],
                    to_hit=f"{a.to_hit:+d}",
                    damage=a.damage,
                    type=t(lang, "dmg." + a.damage_type),
                )
            )
        )
    if cls.casting:
        _, to_hit, dc = characters.spell_stats(char)
        lines.append(
            "🔮 "
            + escape(
                t(
                    lang,
                    "sheet.spellcasting",
                    ability=c.abilities[cls.casting].name.get(lang),
                    to_hit=f"{to_hit:+d}",
                    dc=dc,
                )
            )
        )
    lines.append(t(lang, "sheet.passive_perception", value=10 + characters.skill_bonus(char, skills, "perception")))
    immune = characters.immunities(char)
    if immune:
        lines.append(t(lang, "sheet.immune", list=", ".join(t(lang, "status." + s) for s in immune)))

    lines += _sheet_gear(gear, lang)

    # every skill: ● proficient, ○ practiced, · untrained
    lines += ["", f"<b>{t(lang, 'sheet.skills')}</b>", t(lang, "sheet.skills_legend")]
    for key, skill in c.skills.items():
        row = skills.get(key)
        mark = "●" if row and row.proficient else "○" if row and row.xp else "·"
        rank = "★" * skill_rank(row.xp) if row else ""
        lines.append(
            f"{mark} {escape(skill.name.get(lang))} "
            f"<b>{characters.skill_bonus(char, skills, key):+d}</b> {rank}".rstrip()
        )

    # class abilities: unlocked with uses, locked ones show the level they unlock at
    lines += ["", f"<b>{t(lang, 'sheet.abilities')}</b>"]
    built = characters.effective(char).abilities
    for key, a in {**cls.abilities, **built}.items():  # what you have, then what is still locked
        if key in built:
            lines.append(
                f"✨ <b>{escape(a.name.get(lang))}</b>{_uses(char, key, a)}: {escape(a.description.get(lang))}"
                f" /skill_{key}"
            )
        else:
            lines.append(f"🔒 <i>{t(lang, 'sheet.locked', level=a.level, name=escape(a.name.get(lang)))}</i>")

    # reputation
    reps = await npcs.reputations(session, char)
    if reps:
        lines += ["", f"<b>{t(lang, 'sheet.reputation')}</b>"]
        for fac, value in reps.items():
            lines.append(f"• {escape(c.factions[fac].name.get(lang))}: {value:+d} · {rep_label(value, lang)}")

    # origins
    lines += [
        "",
        f"<b>{t(lang, 'sheet.origins')}</b>",
        f"🧬 <i>{escape(c.lineages[char.lineage].trait_text.get(lang))}</i>",
        f"📖 <i>{escape(characters.background_story(char, lang))}</i>",
    ]

    # professions and gathering masteries
    lines += [
        "",
        professions_line(char, lang),
        "",
        f"<b>{t(lang, 'sheet.hobbies')}</b>",
        *hobby_lines(char, lang),
        "",
        f"<b>{t(lang, 'sheet.masteries')}</b>",
        *mastery_lines(char, lang),
    ]

    # today's AI budget and expedition chronicles
    limit = get_settings().ai_user_daily_calls
    calls, _ = await usage_today(session, char.user_id)
    left = max(0, limit - calls)
    lines += [RULE, t(lang, "sheet.ai_usage", calls=calls, limit=limit, left=left, bar=hp_bar(left, limit))]
    climit = get_settings().ai_user_daily_chronicles
    cused = await chronicles.chronicles_today(session, char.id)
    cleft = max(0, climit - cused)
    lines.append(t(lang, "sheet.chronicles", used=cused, limit=climit, left=cleft, bar=hp_bar(cleft, climit)))

    kb = markup(
        [
            [btn(t(lang, "btn.hero_summary"), cb("hero"))],
            [btn(t(lang, "btn.inventory"), cb("inv")), btn(t(lang, "btn.journal"), cb("jr"))],
            [btn(t(lang, "btn.back"), cb("scene"))],
        ]
    )
    return "\n".join(lines)[:MAX_MESSAGE], kb


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
    body = RULE_NUMBER.sub(lambda m: str(rule_numbers(lang).get(m.group(1), m.group(0))), sec.body.get(lang))
    lines = [f"{sec.icon} <b>{escape(sec.title.get(lang))}</b>", RULE, escape(body)]
    if key == "abilities":  # the six abilities and what each is for, straight from abilities.yaml
        lines.append("")
        lines += [
            f"{a.icon} <b>{escape(a.name.get(lang))}</b>: {escape(a.effect.get(lang))}" for a in c.abilities.values()
        ]
    i = keys.index(key)
    nav = [
        btn(f"◀ {c.rulebook[keys[i - 1]].icon}", cb("rb", keys[i - 1])) if i > 0 else None,
        btn(t(lang, "rulebook.index"), cb("rb", "index")),
        btn(f"{c.rulebook[keys[i + 1]].icon} ▶", cb("rb", keys[i + 1])) if i + 1 < len(keys) else None,
    ]
    return "\n".join(lines)[:MAX_MESSAGE], markup([[b for b in nav if b]])


# ---------------------------------------------------------------- lineages and backgrounds


def lineages_list(lang: str) -> str:
    """/lineage: every lineage with its bonuses, skills and trait."""
    c = get_content()
    lines = [t(lang, "lineages.title"), RULE]
    for lin in c.lineages.values():
        bonuses = " · ".join(
            f"{c.abilities[a].icon} {c.abilities[a].short.get(lang)} {n:+d}" for a, n in lin.bonuses.items()
        )
        lines += [
            f"{lin.icon} <b>{escape(lin.name.get(lang))}</b>",
            f"<i>{escape(lin.description.get(lang))}</i>",
            t(lang, "lineages.bonuses", list=bonuses),
        ]
        if lin.skills:
            lines.append(
                t(lang, "classes.skills", list=escape(", ".join(c.skills[s].name.get(lang) for s in lin.skills)))
            )
        lines += [f"✨ {escape(lin.trait_text.get(lang))}", ""]
    return "\n".join(lines).rstrip()[:MAX_MESSAGE]


def background_line(bg, lang: str) -> str:
    """'🎓 Athletics, Intimidation · 💰 15 · 🎒 Rope'."""
    c = get_content()
    parts = ["🎓 " + ", ".join(c.skills[s].name.get(lang) for s in bg.skills), f"💰 {bg.gold}"]
    if bg.items:
        parts.append(
            "🎒 " + ", ".join(c.items[i].name.get(lang) + (f" ×{n}" if n > 1 else "") for i, n in bg.items.items())
        )
    return escape(" · ".join(parts))


def backgrounds_list(lang: str) -> str:
    """/background: every background with its skills, gold and starting items."""
    c = get_content()
    lines = [t(lang, "backgrounds.title"), RULE]
    for bg in c.backgrounds.values():
        if bg.custom:
            continue
        lines += [
            f"{bg.icon} <b>{escape(bg.name.get(lang))}</b>",
            f"<i>{escape(bg.description.get(lang))}</i>",
            background_line(bg, lang),
            "",
        ]
    lines.append(t(lang, "backgrounds.custom"))
    return "\n".join(lines).rstrip()[:MAX_MESSAGE]


# ---------------------------------------------------------------- classes

CLASS_ICONS = {
    "paladin": "🛡️",
    "rogue": "🗡️",
    "warrior": "⚔️",
    "cleric": "✝️",
    "sorcerer": "🔮",
    "druid": "🌿",
    "bard": "🎻",
    "warlock": "🕯️",
    "barbarian": "🪓",
    "monk": "🥋",
    "ranger": "🏹",
    "artificer": "⚙️",
    "shaman": "🌊",
    "death_knight": "💀",
}


def classes_list(lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Every class with its role, hit die and a tappable /class_<key>."""
    c = get_content()
    lines = [t(lang, "classes.title"), RULE]
    for key, cl in c.classes.items():
        lines += [
            f"{CLASS_ICONS.get(key, '•')} <b>{escape(cl.name.get(lang))}</b> · 🎲 d{cl.hit_die} · /class_{key}",
            f"<i>{escape(cl.description.get(lang))}</i>",
            "",
        ]
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
    lines = [
        f"{CLASS_ICONS.get(key, '•')} <b>{escape(cl.name.get(lang))}</b>",
        f"<i>{escape(cl.description.get(lang))}</i>",
        RULE,
        t(lang, "classes.hit_die", die=cl.hit_die, hp=cl.hit_die),
        t(lang, "classes.primary", ability=escape(c.abilities[cl.primary].name.get(lang))),
    ]
    if cl.casting:
        lines.append(t(lang, "classes.casting", ability=escape(c.abilities[cl.casting].name.get(lang))))
    lines.append(t(lang, "classes.skills", list=escape(", ".join(c.skills[s].name.get(lang) for s in cl.skills))))
    gear = ", ".join(c.items[i].name.get(lang) + (f" ×{n}" if n > 1 else "") for i, n in cl.items.items())
    lines.append(t(lang, "classes.items", list=escape(gear)))

    lines += [RULE, f"<b>{t(lang, 'classes.abilities')}</b>"]
    for akey, a in sorted(cl.abilities.items(), key=lambda kv: kv[1].level):
        mark = ("✅ " if a.level <= char.level else "🔒 ") if mine else ""
        lines += [
            "",
            *ability_block(a, lang, prefix=f"{mark}<b>{t(lang, 'classes.level', level=a.level)}</b> · ", key=akey),
        ]
    mine_branches = [b for b in c.class_specializations.values() if b.class_key == key]
    if mine_branches:
        lines += [
            RULE,
            t(lang, "classes.specializations", level=c.progression.specialization_level),
            " · ".join(escape(b.name.get(lang)) for b in mine_branches),
        ]

    rows = [[btn(t(lang, "btn.classes"), cb("clsl"))]]
    if mine:
        rows[0].append(btn(t(lang, "btn.full_sheet"), cb("sheet")))
    return "\n".join(lines)[:MAX_MESSAGE], markup(rows)
