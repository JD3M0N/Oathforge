"""Shared vocabulary: abilities, DC tiers, statuses, damage types, fallback keys, stations, Strict and Text."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


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
