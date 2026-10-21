"""Field activities: gathering, long stays and tracking. Pure rolls, injectable RNG, no I/O.

Masteries (mining, woodcutting...) are free for everyone and grow 0-5 with use; they are not
d20 skills. Bonus units from rank never give extra XP, so progress cannot snowball.
"""

import random
from dataclasses import dataclass, field

MASTERIES = ("mining", "woodcutting", "herbalism", "skinning", "tracking")  # field masteries
GATHER_SKILLS = (*MASTERIES, "fishing")  # what a place can offer: a mastery, or fishing (a hobby since v0.7.20)
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

RARE_MIN_RANK = 3  # a resource gated behind this rank is the activity's rare find
RARE_CAP = 0.95  # however many bonuses pile up, a rare find is never certain
MIN_SECONDS = 30  # no tool makes an activity shorter than this

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
class Mods:
    """What a tool and a branch change about one activity, fixed when it starts.

    ``rare_rel`` is a relative multiplier on the chance of a rare find (10 % with +5 % is 10.5 %, not 15 %)
    and ``extra_chance`` is rolled once per completed activity, never per unit.
    """

    time_pct: float = 0.0  # 0.10: ten percent shorter
    rare_rel: float = 0.0  # 0.05: five percent more likely, relative to the base chance
    extra_chance: float = 0.0  # chance of one extra unit, once for the whole activity

    def seconds(self, base: int) -> int:
        return max(MIN_SECONDS, round(base * (1 - self.time_pct)))


@dataclass
class GatherRoll:
    items: dict[str, int] = field(default_factory=dict)
    bonus: dict[str, int] = field(default_factory=dict)  # from rank and tools: no XP for these
    rare: str | None = None  # the rare find of this activity, if it came up
    xp: int = 0

    def total(self) -> dict[str, int]:
        out = dict(self.items)
        for k, q in self.bonus.items():
            out[k] = out.get(k, 0) + q
        return out


def available(resources, rank: int) -> list:
    """Resources this rank can find (objects with item, weight and min_rank)."""
    return [r for r in resources if r.min_rank <= rank]


def rare_of(resources, rank: int) -> list:
    """The rare resources this rank can reach: what a selective tool or branch improves the odds of."""
    return [r for r in available(resources, rank) if r.min_rank >= RARE_MIN_RANK]


def rare_chance(resources, rank: int, mode: str, mods: "Mods | None" = None) -> float:
    """The chance that one activity turns up a rare find, before and after its relative bonuses.

    It is the chance the old per-unit table had of giving at least one, so the catalogue keeps its meaning;
    the tool multiplies it instead of adding points, and nothing ever reaches certainty.
    """
    pool = available(resources, rank)
    rares = rare_of(resources, rank)
    if not rares:
        return 0.0
    share = sum(r.weight for r in rares) / sum(r.weight for r in pool)
    units = (GATHER_UNITS if mode == "gather" else STAY_UNITS)[0]
    base = 1 - (1 - share) ** units
    return min(RARE_CAP, base * (1 + (mods.rare_rel if mods else 0.0)))


def roll_gather(rng: random.Random, resources, rank: int, mode: str, mods: "Mods | None" = None) -> GatherRoll:
    """mode 'gather' (5 min, 2-3 units) or 'stay' (15 min, 8-10 units and better XP).

    The rare find is decided once for the whole activity and replaces one common unit, so the percentage the
    help screen announces is the percentage the player gets. Rank and tool bonuses add units without XP.
    """
    pool = available(resources, rank)
    out = GatherRoll()
    if not pool:
        return out
    rares = {r.item for r in rare_of(resources, rank)}
    common_pool = [r for r in pool if r.item not in rares] or pool
    weights = [r.weight for r in common_pool]
    units = rng.randint(*(GATHER_UNITS if mode == "gather" else STAY_UNITS))
    for r in rng.choices(common_pool, weights=weights, k=units):
        out.items[r.item] = out.items.get(r.item, 0) + 1
    if rares and rng.random() < rare_chance(resources, rank, mode, mods):
        found = rng.choices(rare_of(resources, rank), weights=[r.weight for r in rare_of(resources, rank)])[0]
        spent = max(out.items, key=lambda k: out.items[k])  # one common unit becomes the rare one
        out.items[spent] -= 1
        if not out.items[spent]:
            del out.items[spent]
        out.items[found.item] = out.items.get(found.item, 0) + 1
        out.rare = found.item
    common = max(common_pool, key=lambda r: r.weight).item
    for _ in range(BONUS_ROLLS[mode]):
        if rng.random() < bonus_chance(rank):
            out.bonus[common] = out.bonus.get(common, 0) + 1
    if mods and rng.random() < mods.extra_chance:  # one chance for the whole activity, never per unit
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
