"""Dice expressions ("2d6+3", "1d20", "4") and d20 rolls with advantage."""

import random
import re
from dataclasses import dataclass

_DICE_RE = re.compile(r"^\s*(?:(\d*)d(\d+))?\s*([+-]?\s*\d+)?\s*$")


@dataclass(frozen=True)
class DiceExpr:
    count: int
    sides: int
    bonus: int

    @property
    def average(self) -> float:
        return self.count * (self.sides + 1) / 2 + self.bonus


@dataclass(frozen=True)
class RollResult:
    rolls: tuple[int, ...]
    bonus: int

    @property
    def total(self) -> int:
        return max(0, sum(self.rolls) + self.bonus)


@dataclass(frozen=True)
class D20Result:
    rolls: tuple[int, ...]  # one, or two with advantage/disadvantage
    kept: int

    @property
    def nat20(self) -> bool:
        return self.kept == 20

    @property
    def nat1(self) -> bool:
        return self.kept == 1


def parse(expr: str) -> DiceExpr:
    m = _DICE_RE.match(expr)
    if not m or not expr.strip():
        raise ValueError(f"invalid dice expression: {expr!r}")
    count_s, sides_s, bonus_s = m.groups()
    sides = int(sides_s) if sides_s else 0
    count = (int(count_s) if count_s else 1) if sides else 0
    bonus = int(bonus_s.replace(" ", "")) if bonus_s else 0
    return DiceExpr(count, sides, bonus)


def roll(expr: str | DiceExpr, rng: random.Random, crit: bool = False) -> RollResult:
    """Roll an expression. A critical hit doubles the number of dice, not the bonus."""
    d = parse(expr) if isinstance(expr, str) else expr
    count = d.count * 2 if crit else d.count
    return RollResult(tuple(rng.randint(1, d.sides) for _ in range(count)), d.bonus)


def d20(rng: random.Random, advantage: bool = False, disadvantage: bool = False) -> D20Result:
    if advantage and disadvantage:
        advantage = disadvantage = False
    if advantage or disadvantage:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
        return D20Result((a, b), max(a, b) if advantage else min(a, b))
    r = rng.randint(1, 20)
    return D20Result((r,), r)
