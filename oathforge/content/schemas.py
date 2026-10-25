"""Pydantic schemas for the YAML content files.

Every player-facing string is a ``Text`` ({es: ..., en: ...}). Prompt-only
fields (NPC persona, secrets) are plain English strings because only the LLM
reads them.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
DC_TIERS = {"trivial": 5, "easy": 10, "medium": 13, "hard": 16, "very_hard": 19}
STATUSES = (
    "bleeding", "burning", "poisoned", "frightened", "stunned",
    "vulnerable", "hidden", "defending", "blessed",
    "asleep", "restrained", "inspired", "wild_shape", "marked",
)
DamageType = Literal[
    "slashing", "piercing", "bludgeoning", "radiant", "necrotic", "cold", "fire", "poison", "force", "psychic",
]
CreatureType = Literal["humanoid", "beast", "undead"]

Tier = Literal["trivial", "easy", "medium", "hard", "very_hard"]

# how a field activity ended; content/fallbacks/chronicles.yaml has generic texts for each one
CHRONICLE_OUTCOMES = (
    "gather", "stay_ok", "stay_won", "stay_fled", "stay_lost",
    "track_tracks", "track_won", "track_fled", "track_lost",
)
CHRONICLE_PLACEHOLDERS = {"name", "place", "loot", "monster"}

# content/fallbacks/<category>.yaml: what each text may use, and the keys that must exist
FALLBACK_PLACEHOLDERS = {
    "chronicles": CHRONICLE_PLACEHOLDERS,
    "dialogue": {"npc", "name"},
    "narration": {"name", "place"},
    "freetext": {"name"},
}
CHRONICLE_SKILLS = ("mining", "woodcutting", "herbalism", "fishing")
CHRONICLE_KEYS = CHRONICLE_OUTCOMES + tuple(
    f"{outcome}.{skill}" for outcome in CHRONICLE_OUTCOMES[:5] for skill in CHRONICLE_SKILLS
)
FALLBACK_KEYS = {
    "chronicles": CHRONICLE_KEYS,
    "dialogue": ("default",),
    "narration": ("default", "success", "failure", "travel", "steal_success", "steal_failure",
                  "rest", "use_item", "quest", "no_effect", "combat", "victory", "defeat", "fled"),
    "freetext": ("unavailable", "budget_exhausted"),
}

# crafting stations a location can have (Location.stations); each profession works at one, and the
# refining ones (furnace, sawmill, curing_rack, herb_table) belong to a field mastery, not to a profession
Station = Literal[
    "anvil", "alchemy_table", "carpenter_bench", "tannery", "jeweler_bench", "hearth", "scribe_desk", "workbench",
    "loom", "furnace", "sawmill", "curing_rack", "herb_table",
]
T1_MIN_RANK = 3  # a recipe of rank 0-2 is T0; from this rank on it is T1 (see planning/roadmap-profesiones.md)
Row = Literal["front", "back"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Text(Strict):
    es: str
    en: str

    def get(self, lang: str) -> str:
        return getattr(self, lang, None) or self.en


class WorldGuide(Strict):
    summary: Text
    setting: Text
    society: Text
    technology: Text
    magic: Text
    backgrounds: Text

    def context(self, lang: str) -> str:
        return "\n".join((
            self.summary.get(lang), self.setting.get(lang), self.society.get(lang),
            self.technology.get(lang), self.magic.get(lang), self.backgrounds.get(lang),
        ))


class Article(Strict):
    """The article before a place's name in a sentence; empty where the language uses none ("Crownreach Market")."""
    es: str = ""
    en: str = ""


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
    kind: Literal["strike", "spell", "turn", "buff", "surge", "heal", "hide", "save", "curse", "passive",
                  "summon", "command", "converge", "shift"]
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
    status: Literal[
        "blessed", "stunned", "frightened", "asleep", "restrained", "inspired", "wild_shape", "hexed", "marked",
        "vulnerable", "poisoned", "burning", "bleeding",
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
    ranged: bool = False  # strike: with the ranged weapon instead of the melee one
    # a passive: weapon attacks use this ability if it is better than STR/DEX (the Hexblade fights with CHA)
    attack_with: Literal["str", "dex", "int", "wis", "cha"] | None = None
    # spend a status the target carries for extra damage (a mark, a burn, a seal): keeping it ticking is the other
    # choice. The status goes away and `consume_damage` is added; without it the ability is just what it is.
    consumes: Literal["marked", "hexed", "burning", "bleeding", "poisoned", "vulnerable", "restrained", "frightened",
                      "stunned", "asleep"] | None = None
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


class WeaponStats(Strict):
    damage: str
    damage_type: str
    finesse: bool = False
    ranged: bool = False


class RestoreHp(Strict):
    type: Literal["restore_hp"]
    dice: str


class RestoreSpellCharge(Strict):
    """Magic back in the bottle: +``amount`` uses of a spent spell, or +``pool`` of the class's own bar.

    Which one applies depends on the drinker's class, never on the item: a class with a resource
    (GameClass.resource) has no uses to give back.
    """

    type: Literal["restore_spell_charge"]
    amount: int = 1
    pool: int = 0


class ShortRest(Strict):
    """A short rest in a bottle: part of the HP (never past the injury cap) and some of what was spent.

    ``charges`` are uses of a spent ability; ``pool`` is what goes into the class's own bar instead.
    Which one applies depends on the drinker's class, never on the item.
    """

    type: Literal["short_rest"]
    hp_percent: float = 0.20
    charges: int = 1
    pool: int = 0
    cooldown_seconds: int = 4 * 3600


ItemEffect = Annotated[Union[RestoreHp, RestoreSpellCharge, ShortRest], Field(discriminator="type")]


class ItemCombat(Strict):
    """What a consumable does when used in combat (scrolls, bombs). Any class can use it.

    Same shapes as a class ability, with fixed numbers instead of the user's spellcasting:
    spell: ranged attack at ``attack_bonus`` · save: the target (or its row) saves against ``save_dc``
    heal: ``heal_dice`` HP · buff: ``temp_hp`` · escape: leave the fight, no roll.
    """

    kind: Literal["spell", "save", "heal", "buff", "escape"]
    damage: str | None = None
    damage_type: DamageType | None = None
    attack_bonus: int = 5
    save: Literal["dex", "wis"] | None = None
    save_dc: int = 13
    area: Literal["one", "row"] = "one"
    half_on_save: bool = False
    auto_hit: bool = False
    status: Literal["stunned", "frightened", "asleep", "restrained", "burning", "blessed"] | None = None
    status_turns: int = 1
    heal_dice: str | None = None
    temp_hp: str | None = None
    # unused by items, read by the engine's shared ability code
    heal_per_level: int | None = None
    heal_add: None = None
    targets_type: None = None


TYPE_ICONS = {"weapon": "⚔️", "armor": "🛡️", "shield": "🛡️", "consumable": "🧪", "tool": "🧰", "quest": "📜",
              "material": "🧱", "trinket": "💍", "blueprint": "📘"}  # an item without its own icon shows its type's


class ToolProfile(Strict):
    """What a specialized tool does for its discipline: one main advantage, never all three.

    The meaning is the branches': ``rare_rel`` multiplies the chance of a rare find and ``extra_chance``
    is rolled once per completed activity. Only the tool you select counts; owning three adds nothing.
    """

    skill: str  # the field discipline it works for
    base: str | None = None  # the plain tool it replaces (a pickaxe for every miner's pick)
    min_rank: int = Field(0, ge=0, le=5)
    time_pct: float = Field(0.0, ge=0, le=0.5)
    rare_rel: float = Field(0.0, ge=0, le=2)
    extra_chance: float = Field(0.0, ge=0, le=1)


class Item(Strict):
    name: Text
    icon: str | None = None  # 🪨 ores, 🪵 logs, 🌿 herbs…: always next to the name, never instead of it
    description: Text
    # material: gathered or crafted ingredient · trinket: only worth selling (for now)
    # blueprint: teaches one special recipe and is spent doing it
    type: Literal["weapon", "armor", "shield", "consumable", "tool", "quest", "material", "trinket", "blueprint"]
    slot: Literal["main_hand", "ranged", "off_hand", "body"] | None = None
    # T1 gear is crafted by rank and worn by level: a low-level artisan may forge it and not equip it yet
    min_level: int = Field(1, ge=1)
    teaches: str | None = None  # blueprint only: the special recipe it teaches
    tool: ToolProfile | None = None  # a specialized gathering tool: what it changes about its activities
    value: int = 0
    stackable: bool = False
    weapon: WeaponStats | None = None
    base_ac: int | None = None
    dex_cap: int | None = None
    ac_bonus: int = 0
    heal: str | None = None  # also usable in combat (the potion button); outside combat it is a restore_hp effect
    effects: list[ItemEffect] = []  # what "Use" does outside combat
    combat: ItemCombat | None = None  # usable from the combat panel's "Items"
    sellable: bool = True

    def label(self, lang: str) -> str:
        """"🪨 Mena de hierro": its icon (or its type's) and its name."""
        return f"{self.icon or TYPE_ICONS[self.type]} {self.name.get(lang)}"

    def labelled(self) -> dict:
        return {lang: self.label(lang) for lang in ("es", "en")}


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


class BossPattern(Strict):
    """A boss that telegraphs (roadmap_balance §9.1): ``plate`` points of protection that damage wears down before
    its HP, a ``heavy`` attack announced a turn before, and a reload where it is exposed. After ``cycle`` ordinary
    turns it aims; once the plate is gone, after ``cycle_broken``."""

    plate: int = Field(ge=1)
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
    indefinite: Text | None = None  # "un murciélago de cueva" / "a cave bat", for generic texts  # how long /skin takes for one of these (small prey 10 s, more for big ones)
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
    minutes: int = 10  # game minutes on foot: the edge weight of the world graph
    danger: int = Field(0, ge=0, le=3)
    requires_flag: str | None = None
    yards: int | None = Field(None, gt=0)  # distance when the terrain is slow; else minutes × walking pace


class EncounterEntry(Strict):
    monsters: list[str]
    weight: int = 1
    min_level: int = 1  # packs of two start later, so the first levels fight one creature at a time


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


class Healer(Strict):
    cost: int
    heal: str  # dice


class Location(Strict):
    name: Text
    article: Article | None = None  # {es: el, en: the}: «Llegas al Mercado», "You reach the Old Pass Mine"
    description: Text
    night: Text | None = None
    kind: Literal["city", "wild", "dungeon"]
    exits: list[Exit]
    encounters: list[EncounterEntry] = []
    night_encounters: list[EncounterEntry] = []  # replaces `encounters` at night when not empty
    hunting: bool = False  # shows "Hunt" (a fight now) and "Track" (5 min, tracking XP and trophies)
    hunt_day: Text | None = None  # the line before a hunt here; without it a generic one is used
    hunt_night: Text | None = None
    gathering: list[Gathering] = []
    stations: list[Station] = []  # crafting stations here: "Craft" in the scene
    teaches: str | None = None  # the profession learned and swapped here, with its master (one stall per trade)
    home: bool = False  # it grants rooms: your bed and your chest are here
    fixed_encounters: list[FixedEncounter] = []
    scene_objects: dict[str, SceneObject] = {}
    discoveries: dict[str, Discovery] = {}
    rest_cost: int | None = None  # long rest (8 game hours) at an inn
    healer: Healer | None = None  # "Cure wounds" for a few coins (the chapel)
    respawn: bool = False
    hub: bool = False  # the city's plaza: "View city" when the zone has images, and the only way out of the city
    # filled by the loader from the folder: world/<continent>/<zone>/<location>/place.yaml
    zone: str = ""
    continent: str = ""

    def phrase(self) -> dict:
        """The name inside a sentence, with its article: {"es": "el Mercado de Crownreach", "en": "Crownreach Market"}.
        The translator joins «a el» into «al» and «de el» into «del»."""
        return {lang: f"{getattr(self.article, lang) if self.article else ''} {self.name.get(lang)}".strip()
                for lang in ("es", "en")}


class SpecEffects(Strict):
    """What a branch changes about its discipline's activities, with the same meaning as a tool's."""

    time_pct: float = Field(0.0, ge=0, le=0.5)
    rare_rel: float = Field(0.0, ge=0, le=2)
    extra_chance: float = Field(0.0, ge=0, le=1)


class Specialization(Strict):
    """One of the two branches of a field mastery (or of Fishing), chosen at rank 2."""

    skill: str
    name: Text
    description: Text
    effects: SpecEffects = SpecEffects()


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


class Technique(Strict):
    """A group of common recipes that a discipline unlocks on reaching ``rank``, all at once."""

    name: Text
    rank: int = Field(0, ge=0, le=5)


class Profession(Strict):
    """A crafting profession; a character keeps two active (see planning/opificia.md).

    A hobby (cooking) takes no slot: everyone can practise it and level it if they want.
    """

    name: Text
    description: Text
    icon: str
    station: Station | None = None  # where it is crafted
    # a gathering hobby (fishing): no station nor recipes, it levels by doing that field activity
    practice: str | None = None
    hobby: bool = False
    guide: Text | None = None  # how to play it, for /prof_<key>
    techniques: dict[str, Technique] = {}  # unlocked by rank; a recipe says which one it belongs to


class RuleSection(Strict):
    """A page of /rulebook (content/rulebook.yaml)."""
    icon: str
    title: Text
    body: Text  # plain text: it is escaped; /commands in it stay tappable


class Recipe(Strict):
    """A fixed design: exact ingredients, exact outputs. The tier comes from its rank (T1_MIN_RANK).

    ``profession`` is the discipline that gates it and receives its XP: a crafting profession, a hobby,
    or a field mastery when it is a refining recipe (ore -> ingot). ``station`` overrides the discipline's
    own one, which is what lets a mastery refine at the furnace while the smith keeps the anvil.
    """

    profession: str
    station: Station | None = None  # default: the discipline's station
    min_rank: int = Field(0, ge=0, le=5)
    ingredients: dict[str, int]
    outputs: dict[str, int]
    xp: int
    technique: str | None = None  # the group of common recipes it belongs to, unlocked by rank
    special: bool = False  # learned from a blueprint, never by rank
    quest: str | None = None  # a starter recipe: only while that mission is active, and it needs no profession
    installs: Literal["bed", "chest"] | None = None  # furniture: it is set up in your room instead of carried

    @property
    def tier(self) -> int:
        return 1 if self.min_rank >= T1_MIN_RANK else 0

    @field_validator("quest")
    @classmethod
    def _quest_recipes_are_plain(cls, quest, info):
        if quest is not None and (info.data.get("min_rank") or info.data.get("special")):
            raise ValueError("a quest recipe needs no rank and cannot be special")
        return quest


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
    greeting_return: Text | None = None  # instead of `greeting` once the hero has finished one of their missions
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
    # a replacement handed out only while you have neither the material nor what it was for
    unless_item: str | None = None
    unless_furniture: Literal["bed", "chest"] | None = None
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
    # ready: every objective is met and the giver is owed the mission; nothing is paid until then
    state: Literal["locked", "available", "active", "ready", "completed", "failed"] = "active"
    location_text: dict[str, Text] = {}


class QuestObjective(Strict):
    """Counted goal of a mission: kill `count` monsters, talk to an NPC, reach a place, gather, skin or craft
    `count` of an item, finish a long rest, get healed or open a /rulebook section."""

    # kill: monster · talk: npc · visit: location · gather / skin / craft: item obtained (counts quantity)
    # rest / heal: location, or "any" (a long rest that ends / the chapel healer) · read: rulebook section
    # hunt: location (or "any"): a fight won from 🏹 Hunt or 🐾 Track there, any creature, day or night
    # equip / buy / sell / stash / take: item (or "any") · learn_profession: profession · blueprint: the blueprint item
    # smoke: a fight left with a smoke bomb ("any") · branch: the class branch taken (or "any")
    kind: Literal["kill", "hunt", "talk", "visit", "gather", "skin", "craft", "rest", "heal", "read",
                  "equip", "learn_profession", "stash", "take", "buy", "sell", "smoke", "branch", "blueprint",
                  "short_rest"]
    target: str  # monster, npc, location, item or rulebook section key ("any" for hunt / rest / heal)
    count: int = 1


class Quest(Strict):
    name: Text
    summary: Text
    start_stage: str
    # a character who completed any of these (old, removed) quests gets this one completed, without rewards
    legacy_done: list[str] = []
    stages: dict[str, QuestStage]
    actions: dict[str, QuestAction] = {}
    triggers: list[QuestTrigger] = []
    # missions: the journal lists them by `order`; a locked mission opens at `unlock_stage`
    # once the `after` mission is completed or the `unlock_flag` is set
    order: int = 100
    # a tutorial mission (counted by `oath tutorial-stats`); its activities take their real time
    tutorial: bool = False
    giver: str | None = None  # npc
    hint: Text | None = None
    after: str | None = None
    unlock_flag: str | None = None
    unlock_profession: str | None = None  # opens while the hero practises this trade
    unlock_stage: str | None = None
    # all objectives met on `objective_stage` -> rewards, then `complete_stage`.
    # With `turn_in_stage` the mission stops there instead, waiting for `giver` to be paid in person:
    # handing it in pays the rewards and moves it to `complete_stage`, all at once (roadmap_balance §8.1).
    objectives: list[QuestObjective] = []
    objective_stage: str | None = None
    turn_in_stage: str | None = None
    complete_stage: str | None = None
    rewards: list[Effect] = []
