"""Characters: skills, lineages, backgrounds, classes and their abilities, entities, forms, class branches and progression."""

from typing import Literal

from pydantic import Field, field_validator

from oathforge.content.schemas.common import ABILITIES, CreatureType, DamageType, Strict, Text


class Skill(Strict):
    ability: Literal["str", "dex", "con", "int", "wis", "cha"]
    name: Text


class AbilityInfo(Strict):
    name: Text
    short: Text
    effect: Text  # what it does in game, shown while assigning points at creation
    icon: str = ""


class Lineage(Strict):
    name: Text
    icon: str = ""
    description: Text
    bonuses: dict[str, int] = {}
    skills: list[str] = []
    traits: list[Literal["relentless", "poison_resilience", "keen_senses", "versatile"]] = []
    trait_text: Text


class Background(Strict):
    name: Text
    icon: str = ""
    basic: bool = False  # a button straight away at creation; the rest behind "More…"
    custom: bool = False  # the player writes it: name, story and skills come from them
    description: Text
    skills: list[str]
    gold: int
    items: dict[str, int] = {}


EntityKind = Literal["summon", "servant", "companion", "construct", "turret", "totem"]
EntityRole = Literal["damage", "area", "guard", "disrupt"]


class EntityDef(Strict):
    """Something that fights beside the hero on its own: a summon, a servant, a beast, a construct, a turret or
    a totem. It acts by itself, deterministically, once per turn of its owner (roadmap_balance §7).

    Numbers scale with the hero's level when the encounter starts; the entity is never an item and never
    something that can be sold or duplicated.
    """

    name: Text
    description: Text
    kind: EntityKind
    role: EntityRole
    icon: str = "✦"
    hp: int = Field(ge=1)  # a guard's HP are the damage it takes in the hero's place
    hp_per_level: int = Field(0, ge=0)
    to_hit: int = 3  # plus the hero's proficiency
    damage: str | None = None
    damage_type: DamageType | None = None
    ranged: bool = False
    status: Literal["stunned", "frightened", "vulnerable", "poisoned", "restrained"] | None = None
    status_turns: int = Field(1, ge=1)
    period: int = Field(1, ge=1)  # acts every this many turns of its owner
    duration: int | None = Field(None, ge=1)  # turns of its owner it lasts; None: the whole fight

    @field_validator("damage")
    @classmethod
    def _dice(cls, v: str | None) -> str | None:
        if v is not None:
            from oathforge.engine.dice import parse

            parse(v)  # fails on anything that is not dice, so a typo is caught on startup
        return v


class FormAttack(Strict):
    name: Text
    damage: str  # dice; the hero's modifier is added when the fight starts
    damage_type: DamageType
    ability: Literal["str", "dex"] = "str"
    ranged: bool = False


class FormDef(Strict):
    """A shape the hero can take (Shapeshifter). It replaces the attacks and adds a bounded reserve of
    temporary HP the first time it is taken in a fight: switching back and forth never heals."""

    name: Text
    description: Text
    icon: str = "🐾"
    ac_bonus: int = 0
    temp_hp: int = Field(0, ge=0)
    temp_hp_per_level: int = Field(0, ge=0)
    attacks: list[FormAttack] = Field(min_length=1)


class ClassAbility(Strict):
    name: Text
    description: Text
    details: Text | None = None  # longer explanation for /skill_<key>
    level: int
    # strike: weapon attack + extra_damage · spell: ranged spell attack for `damage`
    # turn: `damage` + `status` to every enemy of `targets_type` · buff: `status` on self
    # save: target (or the target's whole row) rolls a saving throw against `damage` / `status`
    # curse: `status` on one enemy, no save (Hex) · surge: bonus action that gives the action back
    # heal · hide · passive
    # summon: calls `entity` for a few turns (never more than the slot allows) · command: `entity` strikes now,
    # with `extra_damage` on top, and does not act again this turn · converge: every entity the hero has is
    # empowered for `boost_turns` · shift: take (or, with form "none", leave) a form
    kind: Literal[
        "strike",
        "spell",
        "turn",
        "buff",
        "surge",
        "heal",
        "hide",
        "save",
        "curse",
        "passive",
        "summon",
        "command",
        "converge",
        "shift",
    ]
    action: Literal["action", "bonus", "none"] = "action"
    uses: int | None = None  # per rest; None = unlimited (classes without a resource bar)
    # classes with their own bar (GameClass.resource) pay with it instead of with uses per rest
    cost: int = Field(0, ge=0)
    generates: int = Field(0, ge=0)  # what using it puts back into the bar
    cooldown: int = Field(0, ge=0)  # turns of combat before it can be used again; never real seconds
    damage: str | None = None
    # a free spell that grows with the hero: from each level on, these dice replace `damage`. Without it the
    # everyday attack of a caster would stay at its level-1 size for ever and the Mana would be all they had.
    damage_tiers: dict[int, str] = {}
    extra_damage: str | None = None
    damage_type: DamageType | None = None
    heal_per_level: int | None = None
    heal_dice: str | None = None
    heal_add: Literal["level", "casting"] | None = None
    status: (
        Literal[
            "blessed",
            "stunned",
            "frightened",
            "asleep",
            "restrained",
            "inspired",
            "wild_shape",
            "hexed",
            "marked",
            "vulnerable",
            "poisoned",
            "burning",
            "bleeding",
        ]
        | None
    ) = None
    status_turns: int = 1
    targets_type: CreatureType | None = None
    save: Literal["dex", "wis"] | None = None  # the target's saving throw (kind: save)
    area: Literal["one", "row"] = "one"  # row: every enemy in the chosen target's row
    half_on_save: bool = False
    auto_hit: bool = False  # spell that never misses (Magic Missile)
    temp_hp: str | None = None  # buff: temporary HP dice (+ heal_add)
    ac_bonus: int = 0
    ac_bonus_unarmored: int = 0  # only without body armor (Mage Armor)
    spell_damage_bonus: bool = False  # passive: add the casting modifier to spell damage
    immune: list[str] = []
    sneak_dice: dict[int, int] = {}  # level -> d6 count
    extra_attack: bool = False
    halve_first_hit: bool = False
    crit_range: int | None = None  # e.g. 19: critical on 19-20
    bonus_damage: str | None = None  # once per turn on a melee weapon hit
    bonus_damage_type: DamageType | None = None
    ranged: bool = False  # strike: with the ranged weapon instead of the melee one
    # a passive: weapon attacks use this ability if it is better than STR/DEX (the Hexblade fights with CHA)
    attack_with: Literal["str", "dex", "int", "wis", "cha"] | None = None
    # spend a status the target carries for extra damage (a mark, a burn, a seal): keeping it ticking is the other
    # choice. The status goes away and `consume_damage` is added; without it the ability is just what it is.
    consumes: (
        Literal[
            "marked",
            "hexed",
            "burning",
            "bleeding",
            "poisoned",
            "vulnerable",
            "restrained",
            "frightened",
            "stunned",
            "asleep",
        ]
        | None
    ) = None
    consume_damage: str | None = None
    leech_pct: int = Field(0, ge=0, le=100)  # heal this share of the real damage this ability dealt
    reduces_cooldowns: int = Field(0, ge=0)  # take this many turns off every OTHER cooldown of the hero
    # a passive that answers a blow: damage back to the attacker, and/or what the bar gets for being hit.
    # Each counts once per attack and only if damage was really taken; the answer never answers itself.
    thorns: str | None = None
    resource_on_hurt: int = Field(0, ge=0)
    entity: str | None = None  # summon / command: the template. A passive with it brings the permanent companion
    form: str | None = None  # shift
    boost_turns: int = Field(3, ge=1)  # converge


class GameClass(Strict):
    name: Text
    description: Text
    hit_die: int
    primary: str
    # featured combat button: the first of these the hero has and can use (the rest go to "✨ Actions")
    signature: list[str] = []
    casting: Literal["int", "wis", "cha"] | None = None  # spell attacks and healing use this modifier
    resource: str | None = None  # its own bar in content/progression.yaml (Conviction, Focus, Mana…)
    resource_on_attack: int = Field(0, ge=0)  # what a basic attack puts into the bar (Fury, Conviction, Focus)
    array: dict[str, int]
    skills: list[str]
    items: dict[str, int]
    equip: list[str]
    abilities: dict[str, ClassAbility]

    @field_validator("array")
    @classmethod
    def _array_complete(cls, v: dict[str, int]) -> dict[str, int]:
        if sorted(v) != sorted(ABILITIES):
            raise ValueError("array must assign every ability")
        return v


MAX_CHARACTER_LEVEL = 20  # T2 and levels 21-30 are a future expansion (roadmap_balance N08)
Role = Literal["dmg", "deff", "heal", "control"]  # the first one in a branch's list is its main role


class ResourceDef(Strict):
    """A class's own bar (Conviction, Focus, Mana…): what it is called and how it comes back.

    ``base`` + ``per_level`` give the maximum; ``per_turn`` is what a combat turn restores and
    ``on_victory`` the share recovered after a won fight. A rest always refills it (see B03).
    """

    name: Text
    description: Text
    base: int = Field(0, ge=0)
    per_level: int = Field(0, ge=0)
    per_turn: int = Field(0, ge=0)
    on_victory: float = Field(0.0, ge=0, le=1)
    starts_empty: bool = False  # Fury and the like begin a fight at zero and are built up


class AbilityPatch(Strict):
    """Fixed numbers a modifier moves on an ability that already exists. Never a formula."""

    cost: int = 0
    cooldown: int = 0
    status_turns: int = 0
    # fixed replacements: the ability keeps its shape, with these dice instead
    damage: str | None = None
    extra_damage: str | None = None
    consume_damage: str | None = None
    heal_dice: str | None = None
    temp_hp: str | None = None
    leech_pct: int | None = None


class Modifier(Strict):
    """One of the two options the hero picks at level 13 and again at 17: fixed, and kept.

    It tunes abilities the hero already has (``patches``) and/or gives a new one (``grants``).
    """

    level: int = Field(ge=1, le=MAX_CHARACTER_LEVEL)
    name: Text
    description: Text
    patches: dict[str, AbilityPatch] = {}
    grants: dict[str, ClassAbility] = {}


class ClassSpecialization(Strict):
    """One of the 41 class branches, chosen at level 10 and kept (see planning/roadmap_balance.md §6).

    It is a different thing from ``Specialization``, which is a branch of a field mastery.
    ``ready`` stays false until the branch has its whole 10-20 path, so it cannot be picked yet:
    the passive and the technique of level 10, the fixed development, two options at each modifier
    level and the culminating technique of level 20.
    """

    class_key: str
    name: Text
    description: Text  # its loop: what decision the branch gives the player
    roles: list[Role] = Field(min_length=1, max_length=2)
    ready: bool = False
    # bumped when an update substantially changes how the branch plays: whoever chose it earlier
    # may then choose again once, for free (roadmap_balance D09)
    revision: int = Field(1, ge=1)
    abilities: dict[str, ClassAbility] = {}  # levels 10-20
    modifiers: dict[str, Modifier] = {}


class TrainingEffects(Strict):
    """What a training package changes in the numbers, so the hero sees HP, attack, DC or bar move."""

    max_hp: int = Field(0, ge=0)
    to_hit: int = Field(0, ge=0)  # weapon and spell attacks
    spell_dc: int = Field(0, ge=0)
    resource_max: int = Field(0, ge=0)


class Training(Strict):
    """A package offered at levels 5, 12 and 18: an offensive one and a resilient or secondary one."""

    name: Text
    description: Text
    effects: TrainingEffects


class Milestone(Strict):
    """A narrative gate: until it is done, no amount of XP takes the hero past ``level_cap``."""

    name: Text
    description: Text
    level_cap: int = Field(ge=1, le=MAX_CHARACTER_LEVEL)
    quest: str | None = None  # the mission whose turn-in grants it


class Progression(Strict):
    """content/progression.yaml: the XP table, the milestone gates and the class resources.

    The hero's level is the lowest of what XP allows, what milestones permit and ``max_level``.
    """

    xp: list[int] = Field(min_length=2)
    training_levels: list[int] = []  # levels that ask the player to pick a training package
    modifier_levels: list[int] = []  # levels that ask for one of the branch's two modifiers
    specialization_level: int = Field(10, ge=1, le=MAX_CHARACTER_LEVEL)
    base_cap: int = Field(MAX_CHARACTER_LEVEL, ge=1, le=MAX_CHARACTER_LEVEL)  # the cap with no milestone done
    milestones: dict[str, Milestone] = {}
    resources: dict[str, ResourceDef] = {}
    trainings: dict[str, Training] = {}  # every training level offers all of them
    # classes approved in roadmap_balance §6 that B06 has not written yet: their branches load and
    # validate, but none of them may be ready, so nobody can pick one.
    future_classes: list[str] = []

    @field_validator("xp")
    @classmethod
    def _rising_from_zero(cls, v: list[int]) -> list[int]:
        if v[0] != 0:
            raise ValueError("the first XP threshold must be 0 (level 1)")
        if any(b <= a for a, b in zip(v, v[1:])):
            raise ValueError("XP thresholds must rise")
        if len(v) > MAX_CHARACTER_LEVEL:
            raise ValueError(f"no more than {MAX_CHARACTER_LEVEL} levels")
        return v
