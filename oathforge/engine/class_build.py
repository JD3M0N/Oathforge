"""The effective build: what a hero can really do at their level, with their branch and their choices.

Pure, like the rest of ``engine/``: everything comes in as arguments (the parsed content and the
hero's own choices) and a ``Build`` comes out. It is the single answer for the combat engine, the
sheet, the rest, the consumables, the simulator and the reports, so that no view keeps a parallel
list of abilities (planning/roadmap_balance.md §3.3).

Levels work the same way: **XP proves experience and a milestone opens a narrative border, and both
are needed**. The effective level is the lowest of what XP allows, what the milestones permit and
the maximum (§4.1).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from oathforge.content.schemas import ClassAbility, ClassSpecialization, GameClass, Modifier, Progression, ResourceDef

TRAINING = "training"
MODIFIER = "modifier"


@dataclass(frozen=True)
class Choice:
    """A pick the hero owes: a training package or one of their branch's two modifiers."""

    kind: str  # TRAINING | MODIFIER
    level: int

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.level}"


@dataclass(frozen=True)
class Build:
    level: int
    class_key: str
    specialization: str | None
    abilities: dict[str, ClassAbility]  # usable now, branch and modifiers included; passives too
    resource: str | None
    resource_max: int  # the bar's top, trainings included
    pending: tuple[Choice, ...]  # choices the hero reached but has not made
    bonuses: dict[str, int] = field(default_factory=dict)  # summed training effects: max_hp, to_hit…

    def usable(self) -> dict[str, ClassAbility]:
        return {k: a for k, a in self.abilities.items() if a.kind != "passive"}

    def passives(self) -> dict[str, ClassAbility]:
        return {k: a for k, a in self.abilities.items() if a.kind == "passive"}


# ------------------------------------------------------------------ levels


def level_for_xp(xp: int, prog: Progression) -> int:
    """The level the hero's experience alone would give them."""
    level = 1
    for lvl, threshold in enumerate(prog.xp, start=1):
        if xp >= threshold:
            level = lvl
    return level


def cap_for(milestones: Iterable[str], prog: Progression) -> int:
    """The highest level the milestones already done allow. Unknown keys are ignored."""
    done = set(milestones)
    caps = [m.level_cap for key, m in prog.milestones.items() if key in done]
    return max([prog.base_cap, *caps])


def eligible_level(xp: int, milestones: Iterable[str], prog: Progression) -> int:
    return min(level_for_xp(xp, prog), cap_for(milestones, prog), len(prog.xp))


def xp_to_next(xp: int, prog: Progression) -> int | None:
    """XP left for the next level, or None at the top. It does not look at milestones: the XP
    keeps counting while the hero waits at a gate, and nothing of it is lost (§4.1)."""
    level = level_for_xp(xp, prog)
    return None if level >= len(prog.xp) else prog.xp[level] - xp


def blocked_by(xp: int, milestones: Iterable[str], prog: Progression) -> str | None:
    """The milestone standing between the hero and the level their XP already earned, if any.
    The journal uses it to tell 'you need XP' apart from 'you need to finish this mission'."""
    if level_for_xp(xp, prog) <= cap_for(milestones, prog):
        return None
    done, cap = set(milestones), cap_for(milestones, prog)
    nxt = [(m.level_cap, key) for key, m in prog.milestones.items() if key not in done and m.level_cap > cap]
    return min(nxt)[1] if nxt else None


# --------------------------------------------------------------- resources


def resource_max(res: ResourceDef, level: int) -> int:
    return res.base + res.per_level * level


# ----------------------------------------------------------------- choices


def pending_choices(
    level: int, taken: Mapping[str, str], prog: Progression, specialized: bool = True
) -> tuple[Choice, ...]:
    """Choices the hero has reached and not made yet. They queue up: skipping several levels at
    once never loses the training of level 5 (§4.4). Modifiers need a branch first."""
    choices = [Choice(TRAINING, lvl) for lvl in prog.training_levels if lvl <= level]
    if specialized:
        choices += [Choice(MODIFIER, lvl) for lvl in prog.modifier_levels if lvl <= level]
    return tuple(sorted((c for c in choices if c.key not in taken), key=lambda c: (c.level, c.kind)))


# ------------------------------------------------------------------- build


def training_bonuses(taken: Mapping[str, str], prog: Progression) -> dict[str, int]:
    """The summed numbers of every training package the hero has taken. Unknown ids add nothing."""
    total: dict[str, int] = {"max_hp": 0, "to_hit": 0, "spell_dc": 0, "resource_max": 0}
    for key, option in taken.items():
        training = prog.trainings.get(option) if key.startswith(f"{TRAINING}:") else None
        if training is not None:
            for name in total:
                total[name] += getattr(training.effects, name)
    return total


def chosen_modifiers(branch: ClassSpecialization, taken: Mapping[str, str]) -> dict[str, Modifier]:
    """The modifiers the hero picked that really belong to ``branch`` at the level they were picked."""
    out = {}
    for key, option in taken.items():
        kind, _, lvl = key.partition(":")
        mod = branch.modifiers.get(option) if kind == MODIFIER and lvl.isdigit() else None
        if mod is not None and mod.level == int(lvl):
            out[option] = mod
    return out


def _patched(ability: ClassAbility, patch) -> ClassAbility:
    """An ability with a modifier's fixed numbers applied: deltas never go below their floor, and replacement
    dice only replace what the ability already had (a patch cannot invent a mechanic)."""
    update = {
        "cost": max(0, ability.cost + patch.cost),
        "cooldown": max(0, ability.cooldown + patch.cooldown),
        "status_turns": max(1, ability.status_turns + patch.status_turns),
    }
    for name in ("damage", "extra_damage", "consume_damage", "heal_dice", "temp_hp"):
        value = getattr(patch, name)
        if value is not None and getattr(ability, name) is not None:
            update[name] = value
    if patch.leech_pct is not None and ability.leech_pct:
        update["leech_pct"] = patch.leech_pct
    return ability.model_copy(update=update)


def _at_level(ability: ClassAbility, level: int) -> ClassAbility:
    """The dice of a growing spell at this level."""
    if not ability.damage_tiers:
        return ability
    reached = [lvl for lvl in ability.damage_tiers if lvl <= level]
    return ability.model_copy(update={"damage": ability.damage_tiers[max(reached)]}) if reached else ability


def build_for(
    class_key: str,
    cls: GameClass,
    level: int,
    prog: Progression,
    *,
    specialization: str | None = None,
    branch: ClassSpecialization | None = None,
    taken: Mapping[str, str] | None = None,
    resource: ResourceDef | None = None,
) -> Build:
    """The hero's effective catalogue: class, branch, modifiers and trainings, all in one place.

    ``branch`` must belong to ``class_key``; a branch that is not ready, or a level below the one where
    branches are chosen, leaves the hero without one. ``taken`` maps each choice (``training:5``,
    ``modifier:13``) to what the hero picked."""
    taken = taken or {}
    if branch is not None and branch.class_key != class_key:
        raise ValueError(f"branch '{specialization}' does not belong to class '{class_key}'")
    if branch is None or not branch.ready or level < prog.specialization_level:
        branch, specialization = None, None
    abilities = {k: a for k, a in cls.abilities.items() if a.level <= level}
    if branch is not None:
        abilities.update({k: a for k, a in branch.abilities.items() if a.level <= level})
        for mod in chosen_modifiers(branch, taken).values():
            for akey, patch in mod.patches.items():
                if akey in abilities:
                    abilities[akey] = _patched(abilities[akey], patch)
            abilities.update({k: a for k, a in mod.grants.items() if a.level <= level})
    abilities = {k: _at_level(a, level) for k, a in abilities.items()}
    bonuses = training_bonuses(taken, prog)
    return Build(
        level=level,
        class_key=class_key,
        specialization=specialization,
        abilities=abilities,
        resource=cls.resource,
        resource_max=resource_max(resource, level) + bonuses["resource_max"] if resource else 0,
        pending=pending_choices(level, taken, prog, specialized=specialization is not None),
        bonuses=bonuses,
    )
