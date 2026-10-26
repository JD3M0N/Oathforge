"""Ability modifiers, proficiency and skill checks."""

import random
from dataclasses import dataclass

from oathforge.content.schemas import DC_TIERS
from oathforge.engine.dice import d20

TIER_ORDER = list(DC_TIERS)  # trivial < easy < medium < hard < very_hard


def modifier(score: int) -> int:
    return (score - 10) // 2


def proficiency_bonus(level: int) -> int:
    return 2 + (max(1, level) - 1) // 4


def dc_for(tier: str) -> int:
    return DC_TIERS[tier]


def clamp_tier(suggested: str | None, minimum: str = "easy", maximum: str = "very_hard") -> str:
    """The LLM may suggest a difficulty; the engine keeps it inside the allowed band."""
    if suggested not in DC_TIERS:
        suggested = "medium"
    lo, hi = TIER_ORDER.index(minimum), TIER_ORDER.index(maximum)
    return TIER_ORDER[min(max(TIER_ORDER.index(suggested), lo), hi)]


@dataclass(frozen=True)
class CheckResult:
    skill: str
    rolls: tuple[int, ...]
    kept: int
    bonus: int
    dc: int

    @property
    def total(self) -> int:
        return self.kept + self.bonus

    @property
    def success(self) -> bool:
        return self.total >= self.dc

    @property
    def margin(self) -> int:
        return self.total - self.dc


def check(
    rng: random.Random, skill: str, bonus: int, dc: int, advantage: bool = False, disadvantage: bool = False
) -> CheckResult:
    r = d20(rng, advantage, disadvantage)
    return CheckResult(skill, r.rolls, r.kept, bonus, dc)
