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
    "asleep", "restrained", "inspired", "wild_shape",
)
DamageType = Literal[
    "slashing", "piercing", "bludgeoning", "radiant", "necrotic", "cold", "fire", "poison", "force", "psychic",
]
CreatureType = Literal["humanoid", "beast", "undead"]

Tier = Literal["trivial", "easy", "medium", "hard", "very_hard"]

# how a field activity ended; content/chronicles.yaml has generic texts for each one
CHRONICLE_OUTCOMES = (
    "gather", "stay_ok", "stay_won", "stay_fled", "stay_lost",
    "track_tracks", "track_won", "track_fled", "track_lost",
)
CHRONICLE_PLACEHOLDERS = {"name", "place", "loot", "monster"}
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
    effect: Text  # what it does in game, shown while assigning points at creation


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
    # save: target (or the target's whole row) rolls a saving throw against `damage` / `status`
    # curse: `status` on one enemy, no save (Hex) · surge: bonus action that gives the action back
    # heal · hide · passive
    kind: Literal["strike", "spell", "turn", "buff", "surge", "heal", "hide", "save", "curse", "passive"]
    action: Literal["action", "bonus", "none"] = "action"
    uses: int | None = None  # per rest; None = unlimited
    damage: str | None = None
    extra_damage: str | None = None
    damage_type: DamageType | None = None
    heal_per_level: int | None = None
    heal_dice: str | None = None
    heal_add: Literal["level", "casting"] | None = None
    status: Literal[
        "blessed", "stunned", "frightened", "asleep", "restrained", "inspired", "wild_shape", "hexed",
    ] | None = None
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
    # material: gathered or crafted ingredient · trinket: only worth selling (for now)
    type: Literal["weapon", "armor", "shield", "consumable", "tool", "quest", "material", "trinket"]
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
    cowardly: bool = False
    immune: list[str] = []  # statuses
    type: CreatureType = "humanoid"
    resist: list[DamageType] = []
    vulnerable: list[DamageType] = []
    immune_damage: list[DamageType] = []
    # bestiary
    lore: Text | None = None
    habitat: Text | None = None
    active: Literal["day", "night", "any"] = "any"


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


class GatherResource(Strict):
    item: str
    weight: int = 1
    min_rank: int = Field(0, ge=0, le=5)  # mastery rank needed to find it


class Gathering(Strict):
    """A field activity here: "Gather" (5 min, safe) and "Stay" (15 min, more loot, may end in an ambush)."""

    skill: Literal["mining", "woodcutting", "herbalism", "fishing"]
    tool: str | None = None  # item needed in the inventory
    resources: list[GatherResource]
    stay_ambush: float = Field(0.0, ge=0, le=1)  # the ambushers come from the place's encounter table


class Location(Strict):
    name: Text
    description: Text
    night: Text | None = None
    kind: Literal["city", "wild", "dungeon"]
    exits: list[Exit]
    encounters: list[EncounterEntry] = []
    night_encounters: list[EncounterEntry] = []  # replaces `encounters` at night when not empty
    hunting: bool = False  # shows "Hunt" (a fight now) and "Track" (5 min, tracking XP and trophies)
    gathering: list[Gathering] = []
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
    state: Literal["locked", "available", "active", "completed", "failed"] = "active"
    location_text: dict[str, Text] = {}


class QuestObjective(Strict):
    """Counted goal of a mission: kill `count` monsters, talk to an NPC, reach a place."""

    kind: Literal["kill", "talk", "visit"]
    target: str  # monster, npc or location key
    count: int = 1


class Quest(Strict):
    name: Text
    summary: Text
    start_stage: str
    stages: dict[str, QuestStage]
    actions: dict[str, QuestAction] = {}
    triggers: list[QuestTrigger] = []
    # missions: the journal lists them by `order`; a locked mission opens at `unlock_stage`
    # once the `after` mission is completed or the `unlock_flag` is set
    order: int = 100
    giver: str | None = None  # npc
    hint: Text | None = None
    after: str | None = None
    unlock_flag: str | None = None
    unlock_stage: str | None = None
    # all objectives met on `objective_stage` -> rewards, then `complete_stage`
    objectives: list[QuestObjective] = []
    objective_stage: str | None = None
    complete_stage: str | None = None
    rewards: list[Effect] = []
