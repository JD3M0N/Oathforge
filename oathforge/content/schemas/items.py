"""Items: weapons, effects, combat use, tools."""

from typing import Annotated, Literal

from pydantic import Field

from oathforge.content.schemas.common import DamageType, Strict, Text


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


ItemEffect = Annotated[RestoreHp | RestoreSpellCharge | ShortRest, Field(discriminator="type")]


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


TYPE_ICONS = {
    "weapon": "⚔️",
    "armor": "🛡️",
    "shield": "🛡️",
    "consumable": "🧪",
    "tool": "🧰",
    "quest": "📜",
    "material": "🧱",
    "trinket": "💍",
    "blueprint": "📘",
}  # an item without its own icon shows its type's


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
        """ "🪨 Mena de hierro": its icon (or its type's) and its name."""
        return f"{self.icon or TYPE_ICONS[self.type]} {self.name.get(lang)}"

    def labelled(self) -> dict:
        return {lang: self.label(lang) for lang in ("es", "en")}
