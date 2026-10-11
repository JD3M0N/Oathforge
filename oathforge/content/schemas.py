"""Pydantic schemas for the YAML content files.

Every player-facing string is a ``Text`` ({es: ..., en: ...}). Prompt-only
fields (NPC persona, secrets) are plain English strings because only the LLM
reads them.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
DC_TIERS = {"trivial": 5, "easy": 10, "medium": 13, "hard": 16, "very_hard": 19}
STATUSES = (
    "bleeding", "burning", "poisoned", "frightened", "stunned",
    "vulnerable", "hidden", "defending", "blessed",
)
DamageType = Literal["slashing", "piercing", "bludgeoning", "radiant", "necrotic", "cold", "fire", "poison"]
CreatureType = Literal["humanoid", "beast", "undead"]

Tier = Literal["trivial", "easy", "medium", "hard", "very_hard"]
Row = Literal["front", "back"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Text(Strict):
    es: str
    en: str

    def get(self, lang: str) -> str:
        return getattr(self, lang, None) or self.en


class Skill(Strict):
    ability: Literal["str", "dex", "con", "int", "wis", "cha"]
    name: Text


class AbilityInfo(Strict):
    name: Text
    short: Text


class Lineage(Strict):
    name: Text
    description: Text
    bonuses: dict[str, int] = {}
    skills: list[str] = []
    traits: list[Literal["relentless", "poison_resilience", "keen_senses", "versatile"]] = []
    trait_text: Text


class Background(Strict):
    name: Text
    description: Text
    skills: list[str]
    gold: int
    items: dict[str, int] = {}


class ClassAbility(Strict):
    name: Text
    description: Text
    level: int
    # strike: weapon attack + extra_damage · spell: ranged spell attack for `damage`
    # turn: `damage` + `status` to every enemy of `targets_type` · buff: `status` on self
    # surge: bonus action that gives the action back · heal · hide · passive
    kind: Literal["strike", "spell", "turn", "buff", "surge", "heal", "hide", "passive"]
    action: Literal["action", "bonus", "none"] = "action"
    uses: int | None = None  # per rest; None = unlimited
    damage: str | None = None
    extra_damage: str | None = None
    damage_type: DamageType | None = None
    heal_per_level: int | None = None
    heal_dice: str | None = None
    heal_add: Literal["level", "casting"] | None = None
    status: Literal["blessed", "stunned", "frightened"] | None = None
    status_turns: int = 1
    targets_type: CreatureType | None = None
    ac_bonus: int = 0
    immune: list[str] = []
    sneak_dice: dict[int, int] = {}  # level -> d6 count
    extra_attack: bool = False
    halve_first_hit: bool = False
    crit_range: int | None = None  # e.g. 19: critical on 19-20
    bonus_damage: str | None = None  # once per turn on a melee weapon hit
    bonus_damage_type: DamageType | None = None


class GameClass(Strict):
    name: Text
    description: Text
    hit_die: int
    primary: str
    casting: Literal["int", "wis", "cha"] | None = None  # spell attacks and healing use this modifier
    array: dict[str, int]
    skills: list[str]
    items: dict[str, int]
    equip: list[str]
    abilities: dict[str, ClassAbility]
    specializations: dict[str, Text] = {}

    @field_validator("array")
    @classmethod
    def _array_complete(cls, v: dict[str, int]) -> dict[str, int]:
        if sorted(v) != sorted(ABILITIES):
            raise ValueError("array must assign every ability")
        return v


class WeaponStats(Strict):
    damage: str
    damage_type: str
    finesse: bool = False
    ranged: bool = False


class Item(Strict):
    name: Text
    description: Text
    type: Literal["weapon", "armor", "shield", "consumable", "tool", "quest"]
    slot: Literal["main_hand", "ranged", "off_hand", "body"] | None = None
    value: int = 0
    stackable: bool = False
    weapon: WeaponStats | None = None
    base_ac: int | None = None
    dex_cap: int | None = None
    ac_bonus: int = 0
    heal: str | None = None
    sellable: bool = True


class StatusApply(Strict):
    status: Literal[
        "bleeding", "burning", "poisoned", "frightened", "stunned", "vulnerable",
    ]
    turns: int
    chance: float = 1.0


class MonsterAttack(Strict):
    name: Text
    to_hit: int
    damage: str
    damage_type: str
    ranged: bool = False
    applies: StatusApply | None = None


class LootEntry(Strict):
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
    cowardly: bool = False
    immune: list[str] = []  # statuses
    type: CreatureType = "humanoid"
    resist: list[DamageType] = []
    vulnerable: list[DamageType] = []
    immune_damage: list[DamageType] = []


class SceneEffect(Strict):
    damage: str | None = None
    damage_type: str = "bludgeoning"
    targets: Literal["one", "all_enemies"] = "one"
    status: StatusApply | None = None


class SceneObject(Strict):
    name: Text
    description: Text
    skill: str
    tier: Tier
    effect: SceneEffect


class Exit(Strict):
    to: str
    minutes: int = 10
    danger: int = Field(0, ge=0, le=3)
    requires_flag: str | None = None


class EncounterEntry(Strict):
    monsters: list[str]
    weight: int = 1


class FixedEncounter(Strict):
    monsters: list[str]
    flag: str  # set when cleared, so it only happens once per character
    unless_flag: str | None = None
    if_flag: str | None = None


class Discovery(Strict):
    skill: str
    tier: Tier
    text: Text
    sets_flag: str
    gives: dict[str, int] = {}
    gold: int = 0
    requires_flag: str | None = None


class Location(Strict):
    name: Text
    description: Text
    night: Text | None = None
    kind: Literal["city", "wild", "dungeon"]
    exits: list[Exit]
    encounters: list[EncounterEntry] = []
    fixed_encounters: list[FixedEncounter] = []
    scene_objects: dict[str, SceneObject] = {}
    discoveries: dict[str, Discovery] = {}
    rest_cost: int | None = None
    respawn: bool = False
    hub: bool = False  # the zone's overview point (city plaza): shows "View city" when the zone has images
    # filled by the loader from the folder: world/<continent>/<zone>/<location>/place.yaml
    zone: str = ""
    continent: str = ""


class Zone(Strict):
    """A city, a wild area or a dungeon: a group of locations sharing images and audio."""

    name: Text
    description: Text
    night: Text | None = None
    kind: Literal["city", "wilds", "dungeon"]


class Continent(Strict):
    name: Text
    description: Text


class Shop(Strict):
    items: list[str]
    buys: bool = True


class Npc(Strict):
    name: Text
    title: Text
    faction: str | None = None
    schedule: dict[Literal["day", "night"], str]
    greeting: Text
    persona: str
    goals: str
    secrets: str
    knowledge: str
    passive_perception: int = 10
    steal_gold: str | None = None
    shop: Shop | None = None


class Faction(Strict):
    name: Text
    description: Text


Effect = dict[str, object]  # validated by quests.apply_effect at load time


class QuestCheck(Strict):
    skill: str
    tier: Tier
    success_text: Text
    failure_text: Text
    success_effects: list[Effect] = []
    failure_effects: list[Effect] = []


class QuestAction(Strict):
    label: Text
    text: Text
    location: str | None = None
    npc: str | None = None
    stages: list[str]
    requires_item: str | None = None
    check: QuestCheck | None = None
    effects: list[Effect] = []
    to_stage: str


class QuestTrigger(Strict):
    event: Literal["defeat"]
    target: str
    stages: list[str]
    to_stage: str
    text: Text
    effects: list[Effect] = []


class QuestStage(Strict):
    journal: Text
    state: Literal["available", "active", "completed", "failed"] = "active"
    location_text: dict[str, Text] = {}


class Quest(Strict):
    name: Text
    summary: Text
    start_stage: str
    stages: dict[str, QuestStage]
    actions: dict[str, QuestAction]
    triggers: list[QuestTrigger] = []
