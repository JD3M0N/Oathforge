"""Field activities: gathering, long stays and tracking. Pure rolls, injectable RNG, no I/O.

Masteries (mining, woodcutting...) are free for everyone and grow 0-5 with use; they are not
d20 skills. Bonus units from rank never give extra XP, so progress cannot snowball.
"""

import random
from dataclasses import dataclass, field

MASTERIES = ("mining", "woodcutting", "herbalism", "skinning", "fishing", "tracking")
HOBBIES = ("fishing",)  # masteries shown as an optional hobby (with cooking), not as a field mastery
RANK_XP = (0, 80, 240, 500, 900, 1500)  # accumulated XP for ranks 0..5
MAX_RANK = len(RANK_XP) - 1

GATHER_SECONDS = 5 * 60
STAY_SECONDS = 15 * 60
TRACK_SECONDS = 5 * 60
REST_SECONDS = 80 * 60  # a long rest: 8 game hours (a game day lasts 4 real hours)
SECONDS = {"gather": GATHER_SECONDS, "stay": STAY_SECONDS, "track": TRACK_SECONDS, "rest": REST_SECONDS}

GATHER_UNITS = (2, 3)
STAY_UNITS = (8, 10)
GATHER_XP = 10
STAY_XP = (25, 30)
BONUS_PER_RANK = 0.04
BONUS_CAP = 0.20
BONUS_ROLLS = {"gather": 1, "stay": 3}

TRACK_PREY_CHANCE = 0.75
TRACK_XP_TRACKS = 10  # found only tracks: a little XP for the effort
TRACK_XP_WIN = 18
SKIN_XP = 6  # per beast skinned
SKIN_BONUS_PER_RANK = 0.04


def rank_for(xp: int) -> int:
    return max(r for r, need in enumerate(RANK_XP) if xp >= need)


def next_threshold(xp: int) -> int | None:
    """XP needed for the next rank, or None at the top."""
    rank = rank_for(xp)
    return RANK_XP[rank + 1] if rank < MAX_RANK else None


def bonus_chance(rank: int) -> float:
    return min(BONUS_CAP, rank * BONUS_PER_RANK)


@dataclass
class GatherRoll:
    items: dict[str, int] = field(default_factory=dict)
    bonus: dict[str, int] = field(default_factory=dict)  # from rank: no XP for these
    xp: int = 0

    def total(self) -> dict[str, int]:
        out = dict(self.items)
        for k, q in self.bonus.items():
            out[k] = out.get(k, 0) + q
        return out


def available(resources, rank: int) -> list:
    """Resources this rank can find (objects with item, weight and min_rank)."""
    return [r for r in resources if r.min_rank <= rank]


def roll_gather(rng: random.Random, resources, rank: int, mode: str) -> GatherRoll:
    """mode 'gather' (5 min, 2-3 units) or 'stay' (15 min, 8-10 units and better XP)."""
    pool = available(resources, rank)
    out = GatherRoll()
    if not pool:
        return out
    weights = [r.weight for r in pool]
    units = rng.randint(*(GATHER_UNITS if mode == "gather" else STAY_UNITS))
    for r in rng.choices(pool, weights=weights, k=units):
        out.items[r.item] = out.items.get(r.item, 0) + 1
    common = max(pool, key=lambda r: r.weight).item
    for _ in range(BONUS_ROLLS[mode]):
        if rng.random() < bonus_chance(rank):
            out.bonus[common] = out.bonus.get(common, 0) + 1
    out.xp = GATHER_XP if mode == "gather" else rng.randint(*STAY_XP)
    return out


def roll_harvest(rng: random.Random, entries, rank: int) -> dict[str, int]:
    """Skinning a beast: each entry (item, qty, chance) rolls once; rank adds a little chance."""
    out: dict[str, int] = {}
    for e in entries:
        if rng.random() < min(1.0, e.chance + rank * SKIN_BONUS_PER_RANK):
            out[e.item] = out.get(e.item, 0) + e.qty
    return out


def roll_ambush(rng: random.Random, chance: float) -> bool:
    return chance > 0 and rng.random() < chance


def roll_prey(rng: random.Random) -> bool:
    return rng.random() < TRACK_PREY_CHANCE


def half(items: dict[str, int]) -> dict[str, int]:
    """What a stay keeps after fleeing an ambush."""
    return {k: q // 2 for k, q in items.items() if q // 2 > 0}
