"""D&D point buy for ability scores at character creation.

Every score starts at 8 and the player spends 27 points; higher scores cost more
(14 -> 15 costs 2). The standard array 15/14/13/12/10/8 costs exactly 27, so a
class's recommended array is always a legal buy. Lineage bonuses apply on top.
"""

ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
COST = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
BUDGET = 27
MIN_SCORE, MAX_SCORE = min(COST), max(COST)


def base() -> dict[str, int]:
    return {a: MIN_SCORE for a in ABILITIES}


def spent(scores: dict[str, int]) -> int:
    return sum(COST[scores[a]] for a in ABILITIES)


def left(scores: dict[str, int]) -> int:
    return BUDGET - spent(scores)


def valid(scores: dict[str, int]) -> bool:
    return sorted(scores) == sorted(ABILITIES) and all(s in COST for s in scores.values()) and spent(scores) <= BUDGET


def can_raise(scores: dict[str, int], ability: str) -> bool:
    s = scores[ability]
    return s < MAX_SCORE and COST[s + 1] - COST[s] <= left(scores)


def can_lower(scores: dict[str, int], ability: str) -> bool:
    return scores[ability] > MIN_SCORE


def change(scores: dict[str, int], ability: str, delta: int) -> dict[str, int]:
    """A copy with one step up (+1) or down (-1); unchanged when the step is not allowed."""
    if (
        ability not in ABILITIES
        or (delta > 0 and not can_raise(scores, ability))
        or (delta < 0 and not can_lower(scores, ability))
    ):
        return dict(scores)
    return {**scores, ability: scores[ability] + (1 if delta > 0 else -1)}
