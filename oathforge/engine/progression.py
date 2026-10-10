"""Character levels and use-based skill improvement."""

XP_THRESHOLDS = (0, 300, 900, 2700, 6500)
MAX_LEVEL = len(XP_THRESHOLDS)
SKILL_XP_PER_RANK = 100
MAX_SKILL_RANK = 3
SKILL_GAIN = {"easy": 10, "medium": 15, "hard": 20, "very_hard": 30}
RECENT_WINDOW_SECONDS = 24 * 3600


def level_for_xp(xp: int) -> int:
    level = 1
    for lvl, threshold in enumerate(XP_THRESHOLDS, start=1):
        if xp >= threshold:
            level = lvl
    return level


def xp_to_next(xp: int) -> int | None:
    level = level_for_xp(xp)
    return None if level >= MAX_LEVEL else XP_THRESHOLDS[level] - xp


def max_hp(hit_die: int, con_mod: int, level: int) -> int:
    first = hit_die + con_mod
    per_level = hit_die // 2 + 1 + con_mod
    return max(1, first + max(0, per_level) * (level - 1))


def skill_rank(skill_xp: int) -> int:
    return min(MAX_SKILL_RANK, skill_xp // SKILL_XP_PER_RANK)


def skill_gain(tier: str, recent_repeats: int) -> int:
    """XP for a successful check. Trivial checks teach nothing; repeating the
    same thing in a short window halves the gain each time."""
    base = SKILL_GAIN.get(tier, 0)
    return int(base * 0.5 ** recent_repeats)
