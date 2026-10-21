"""Hit points and use-based skill improvement.

The XP table, the milestone gates and the effective catalogue live in ``engine/class_build.py``
and ``content/progression.yaml``: the hero's level needs both experience and a narrative gate.
"""

SKILL_XP_PER_RANK = 100
MAX_SKILL_RANK = 3
SKILL_GAIN = {"easy": 10, "medium": 15, "hard": 20, "very_hard": 30}
RECENT_WINDOW_SECONDS = 24 * 3600


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
