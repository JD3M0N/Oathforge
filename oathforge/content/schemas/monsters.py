"""Monsters: attacks, boss patterns, loot and harvest."""

from typing import Literal

from pydantic import Field

from oathforge.content.schemas.common import CreatureType, DamageType, Row, Strict, Text


class StatusApply(Strict):
    status: Literal["bleeding", "burning", "poisoned", "frightened", "stunned", "vulnerable"]
    turns: int
    chance: float = 1.0


class MonsterAttack(Strict):
    name: Text
    to_hit: int
    damage: str
    damage_type: str
    ranged: bool = False
    applies: StatusApply | None = None


class BossPattern(Strict):
    """A boss that telegraphs (roadmap_balance §9.1): ``plate`` points of protection that damage wears down before
    its HP, a ``heavy`` attack announced a turn before, and a reload where it is exposed. After ``cycle`` ordinary
    turns it aims; once the plate is gone, after ``cycle_broken``."""

    plate: int = Field(ge=1)
    rearm: int = Field(0, ge=0)  # the plate hardens again, once, when the boss is down to half its HP
    cycle: int = Field(2, ge=1)
    cycle_broken: int = Field(1, ge=1)
    heavy: MonsterAttack


class LootEntry(Strict):
    item: str
    chance: float
    qty: int = 1


class HarvestEntry(Strict):
    """What skinning a defeated beast can give (needs a skinning knife)."""

    item: str
    chance: float
    qty: int = 1


class Monster(Strict):
    name: Text
    description: Text
    hp: int
    ac: int
    dex: int  # modifier
    wis: int = 0  # modifier, for passive perception
    row: Row = "front"
    attacks: list[MonsterAttack]
    xp: int
    gold: str = "0"
    loot: list[LootEntry] = []
    harvest: list[HarvestEntry] = []
    skin_seconds: int = 10
    indefinite: Text | None = (
        None  # "un murciélago de cueva" / "a cave bat", for generic texts  # how long /skin takes for one of these (small prey 10 s, more for big ones)
    )
    cowardly: bool = False
    immune: list[str] = []  # statuses
    # a boss never goes down to a control chain: hard control lasts one turn on it and the rest of the
    # duration becomes `vulnerable`, said out loud in the log. Never a silent immunity (roadmap_balance §5.3).
    boss: bool = False
    pattern: BossPattern | None = None
    type: CreatureType = "humanoid"
    resist: list[DamageType] = []
    vulnerable: list[DamageType] = []
    immune_damage: list[DamageType] = []
    # bestiary
    icon: str | None = None  # its own emoji; None: the one for its type
    lore: Text | None = None
    habitat: Text | None = None
    active: Literal["day", "night", "any"] = "any"
