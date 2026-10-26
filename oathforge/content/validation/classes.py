"""Abilities, lineages, backgrounds and classes; their progression, branches, entities and forms."""

from typing import TYPE_CHECKING

from oathforge.content.schemas import ABILITIES, ClassSpecialization
from oathforge.content.validation.common import collector
from oathforge.engine import class_build, dice

if TYPE_CHECKING:
    from oathforge.content.loader import Content


def class_errors(c: "Content") -> list[str]:
    """Lineages, backgrounds and classes point at real skills, items and abilities."""
    errors, need = collector()
    if sorted(c.abilities) != sorted(ABILITIES):
        errors.append("abilities.yaml must define exactly the six abilities")
    for key, lin in c.lineages.items():
        for s in lin.skills:
            need("skill", s, c.skills, f"lineage {key}")
        for a in lin.bonuses:
            need("ability", a, c.abilities, f"lineage {key}")
    for key, bg in c.backgrounds.items():
        for s in bg.skills:
            need("skill", s, c.skills, f"background {key}")
        for i in bg.items:
            need("item", i, c.items, f"background {key}")
    for key, cls in c.classes.items():
        for s in cls.skills:
            need("skill", s, c.skills, f"class {key}")
        for i in [*cls.items, *cls.equip]:
            need("item", i, c.items, f"class {key}")
        need("ability", cls.primary, c.abilities, f"class {key}")
    for key, cls in c.classes.items():
        for a in cls.signature:
            need("ability", a, cls.abilities, f"class {key} signature")
    errors += _class_progression_errors(c)
    return errors


def _class_progression_errors(c: "Content") -> list[str]:
    """The two families of branches must not get mixed up: ``specializations`` are field masteries
    and ``class_specializations`` are the 41 class branches of planning/roadmap_balance.md §6."""
    errors: list[str] = []
    prog = c.progression
    if prog is None:
        return ["progression.yaml: missing"]
    for lvl in [*prog.training_levels, *prog.modifier_levels, prog.specialization_level]:
        if not 1 <= lvl <= len(prog.xp):
            errors.append(f"progression: level {lvl} is outside the 1-{len(prog.xp)} table")
    if set(prog.training_levels) & set(prog.modifier_levels):
        errors.append("progression: a level cannot ask for a training and a modifier at once")
    if any(lvl < prog.specialization_level for lvl in prog.modifier_levels):
        errors.append(f"progression: a modifier is picked before the branch (level {prog.specialization_level})")
    for key, milestone in prog.milestones.items():
        if milestone.quest is not None and milestone.quest not in c.quests:
            errors.append(f"milestone {key}: unknown quest '{milestone.quest}'")
        if milestone.level_cap <= prog.base_cap:
            errors.append(f"milestone {key}: its cap {milestone.level_cap} opens nothing over the base {prog.base_cap}")
    future = set(prog.future_classes)
    if future & set(c.classes):
        errors.append(f"progression: {sorted(future & set(c.classes))} already exist, they are not future classes")
    for key, cls in c.classes.items():
        if cls.resource is not None and cls.resource not in prog.resources:
            errors.append(f"class {key}: unknown resource '{cls.resource}'")
        if cls.resource is None and cls.resource_on_attack:
            errors.append(f"class {key}: it generates on attack but has no bar to put it in")
        for akey, a in cls.abilities.items():
            errors += _ability_errors(prog, cls.resource, f"class {key} ability {akey}", key, a)
    if prog.training_levels and not prog.trainings:
        errors.append("progression: there are training levels but no training packages")
    clash = set(c.class_specializations) & set(c.specializations)
    if clash:
        errors.append(f"class branch and mastery branch share an id: {sorted(clash)}")
    branches: dict[str, list[str]] = {}
    for key, branch in c.class_specializations.items():
        if branch.class_key not in c.classes and branch.class_key not in future:
            errors.append(f"class branch {key}: unknown class '{branch.class_key}'")
        elif branch.class_key in future and branch.ready:
            errors.append(f"class branch {key}: its class '{branch.class_key}' does not exist yet, it cannot be ready")
        branches.setdefault(branch.class_key, []).append(key)
        errors += _branch_errors(c, prog, key, branch)
    errors += _unique_ability_errors(c)
    errors += _entity_errors(c)
    for key in c.classes:
        if c.class_specializations and key not in branches:
            errors.append(f"class {key}: it has no branch to choose at level {prog.specialization_level}")
    return errors


def _ability_errors(prog, resource: str | None, where: str, owner: str, a) -> list[str]:
    """What an ability may cost, whoever owns it: a class, a branch or a modifier."""
    errors = []
    if a.kind == "passive" and (a.cost or a.generates or a.cooldown):
        errors.append(f"{where}: a passive neither costs nor generates nor cools down")
    if bool(a.consumes) != bool(a.consume_damage):
        errors.append(f"{where}: consumes and consume_damage go together")
    if a.consumes and a.kind not in ("strike", "spell", "save"):
        errors.append(f"{where}: only a strike, spell or save can consume a status")
    if a.leech_pct and a.kind not in ("strike", "spell", "save"):
        errors.append(f"{where}: only a strike, spell or save can leech")
    if (a.thorns or a.resource_on_hurt) and a.kind != "passive":
        errors.append(f"{where}: thorns and resource_on_hurt answer a blow, so they belong to a passive")
    if a.reduces_cooldowns and a.kind == "passive":
        errors.append(f"{where}: a passive cannot cut cooldowns")
    if a.damage_tiers:
        if not a.damage:
            errors.append(f"{where}: damage_tiers need a base damage to grow from")
        for lvl, expr in a.damage_tiers.items():
            try:
                dice.parse(expr)
            except ValueError:
                errors.append(f"{where}: damage tier {lvl} is not dice")
    if a.attack_with and a.kind != "passive":
        errors.append(f"{where}: attack_with is a trait, so it belongs to a passive")
    for dice_field in ("consume_damage", "thorns"):
        if getattr(a, dice_field):
            try:
                dice.parse(getattr(a, dice_field))
            except ValueError:
                errors.append(f"{where}: {dice_field} is not dice")
    if resource is None and (a.cost or a.generates):
        errors.append(f"{where}: it uses a bar, but {owner} has none")
    if resource is not None and a.uses is not None:
        errors.append(f"{where}: {owner} pays with {resource}, not with uses per rest")
    top = class_build.resource_max(prog.resources[resource], a.level) if resource in prog.resources else 0
    if resource is not None and a.cost > top:
        errors.append(f"{where}: it costs {a.cost}, more than the {top} the bar holds at level {a.level}")
    return errors


def _branch_errors(c: "Content", prog, key: str, branch: ClassSpecialization) -> list[str]:
    """A branch is playable only with its whole 10-20 path (roadmap_balance §5.2 and §13.1)."""
    errors: list[str] = []
    cls = c.classes.get(branch.class_key)
    resource = cls.resource if cls else None
    first, last = prog.specialization_level, len(prog.xp)
    for akey, a in branch.abilities.items():
        where = f"class branch {key} ability {akey}"
        if a.level < first:
            errors.append(f"{where}: a branch gives nothing before level {first}")
        errors += _ability_errors(prog, resource, where, branch.class_key, a)
    known = set(branch.abilities) | (set(cls.abilities) if cls else set())
    for mkey, mod in branch.modifiers.items():
        where = f"class branch {key} modifier {mkey}"
        if mod.level not in prog.modifier_levels:
            errors.append(f"{where}: level {mod.level} is not one of the modifier levels {prog.modifier_levels}")
        pool = {**(cls.abilities if cls else {}), **branch.abilities}
        for target, patch in mod.patches.items():
            if target not in known:
                errors.append(f"{where}: it tunes '{target}', which the branch does not have")
                continue
            for field in ("damage", "extra_damage", "consume_damage", "heal_dice", "temp_hp"):
                if getattr(patch, field) is not None and getattr(pool[target], field) is None:
                    errors.append(f"{where}: it replaces {field} of '{target}', which has none to replace")
            if patch.leech_pct is not None and not pool[target].leech_pct:
                errors.append(f"{where}: it changes the leech of '{target}', which does not leech")
        for akey, a in mod.grants.items():
            if a.level < mod.level:
                errors.append(f"{where}: it grants '{akey}' at level {a.level}, before its own level {mod.level}")
            errors += _ability_errors(prog, resource, f"{where} grants {akey}", branch.class_key, a)
    if not branch.ready:
        return errors
    live = [a for a in branch.abilities.values()]
    if not any(a.level == first and a.kind == "passive" for a in live):
        errors.append(f"class branch {key}: ready, but it has no passive for level {first}")
    if not any(a.level == first and a.kind != "passive" for a in live):
        errors.append(f"class branch {key}: ready, but it has no technique for level {first}")
    if not any(a.level == last and a.kind != "passive" for a in live):
        errors.append(f"class branch {key}: ready, but it has no culminating technique for level {last}")
    for lvl in prog.modifier_levels:
        n = sum(1 for m in branch.modifiers.values() if m.level == lvl)
        if n != 2:
            errors.append(f"class branch {key}: ready, but level {lvl} has {n} modifiers, not two")
    return errors


def _every_ability(c: "Content"):
    """(where, ability) for every ability anyone can have: classes, branches and what modifiers grant."""
    for ckey, cls in c.classes.items():
        for akey, a in cls.abilities.items():
            yield f"class {ckey} ability {akey}", a
    for bkey, branch in c.class_specializations.items():
        for akey, a in branch.abilities.items():
            yield f"class branch {bkey} ability {akey}", a
        for mkey, mod in branch.modifiers.items():
            for akey, a in mod.grants.items():
                yield f"class branch {bkey} modifier {mkey} grants {akey}", a


def _entity_errors(c: "Content") -> list[str]:
    """Summons, commands, convergences and shifts must point at things that exist (roadmap_balance §7)."""
    errors: list[str] = []
    for key, e in c.entities.items():
        if e.role in ("damage", "area") and not e.damage:
            errors.append(f"entity {key}: a {e.role} entity needs damage")
        if e.role == "disrupt" and not e.status:
            errors.append(f"entity {key}: a disrupt entity needs a status")
        if e.role == "guard" and (e.damage or e.status):
            errors.append(f"entity {key}: a guard only absorbs, it neither hits nor afflicts")
        if e.kind in ("servant", "companion") and e.duration is not None:
            errors.append(f"entity {key}: a permanent being does not expire")
        if e.kind == "summon" and e.duration is None:
            errors.append(f"entity {key}: a summon lasts a while, it needs a duration")
    for where, a in _every_ability(c):
        if a.kind in ("summon", "command"):
            if a.entity not in c.entities:
                errors.append(f"{where}: {a.kind} needs a known entity, not '{a.entity}'")
            elif a.kind == "summon" and c.entities[a.entity].kind in ("servant", "companion"):
                errors.append(f"{where}: a permanent being is brought by a passive, not summoned")
        elif a.kind == "passive" and a.entity is not None:
            if a.entity not in c.entities or c.entities[a.entity].kind not in ("servant", "companion"):
                errors.append(f"{where}: a passive with an entity brings a servant or a companion, not '{a.entity}'")
        elif a.entity is not None:
            errors.append(f"{where}: only summon, command and a passive take an entity")
        if a.kind == "shift" and a.form != "none" and a.form not in c.forms:
            errors.append(f"{where}: shift needs a known form (or 'none'), not '{a.form}'")
        if a.kind != "shift" and a.form is not None:
            errors.append(f"{where}: only shift takes a form")
    return errors


def _unique_ability_errors(c: "Content") -> list[str]:
    """A branch never reuses the key of another ability: the logs, /skill_<key> and the buttons would not
    know which one is meant. (Classes may share a key on purpose, like Extra Attack.)"""
    owners: dict[str, set[str]] = {}
    for ckey, cls in c.classes.items():
        for akey in cls.abilities:
            owners.setdefault(akey, set()).add(f"class {ckey}")
    errors = []
    for bkey, branch in c.class_specializations.items():
        mine = [*branch.abilities, *(k for m in branch.modifiers.values() for k in m.grants)]
        for akey in mine:
            other = owners.get(akey, set()) - {f"branch {bkey}"}
            if other:
                errors.append(f"ability '{akey}' of branch {bkey} is already defined by {sorted(other)[0]}")
            owners.setdefault(akey, set()).add(f"branch {bkey}")
    return errors
