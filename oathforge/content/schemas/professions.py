"""Masteries and professions: specializations, techniques and recipes."""

from typing import Literal

from pydantic import Field, field_validator

from oathforge.content.schemas.common import T1_MIN_RANK, Station, Strict, Text


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
