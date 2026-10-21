import random

import pytest

from oathforge.engine import checks, progression
from oathforge.engine.dice import d20, parse, roll


@pytest.mark.parametrize(
    "expr,count,sides,bonus",
    [("2d6+3", 2, 6, 3), ("d20", 1, 20, 0), ("1d4-1", 1, 4, -1), ("5", 0, 0, 5), ("3d8 + 2", 3, 8, 2)],
)
def test_parse(expr, count, sides, bonus):
    d = parse(expr)
    assert (d.count, d.sides, d.bonus) == (count, sides, bonus)


@pytest.mark.parametrize("bad", ["", "abc", "2d", "d6d6"])
def test_parse_rejects(bad):
    with pytest.raises(ValueError):
        parse(bad)


def test_roll_bounds_and_crit_doubles_dice():
    rng = random.Random(1)
    for _ in range(200):
        r = roll("2d6+3", rng)
        assert 5 <= r.total <= 15 and len(r.rolls) == 2
    assert len(roll("2d6+3", rng, crit=True).rolls) == 4


def test_roll_total_never_negative():
    rng = random.Random(0)
    assert all(roll("1d4-10", rng).total == 0 for _ in range(20))


def test_d20_advantage_and_disadvantage():
    rng = random.Random(7)
    for _ in range(100):
        a = d20(rng, advantage=True)
        assert len(a.rolls) == 2 and a.kept == max(a.rolls)
        d = d20(rng, disadvantage=True)
        assert d.kept == min(d.rolls)
        both = d20(rng, advantage=True, disadvantage=True)
        assert len(both.rolls) == 1


@pytest.mark.parametrize("score,mod", [(1, -5), (8, -1), (9, -1), (10, 0), (11, 0), (12, 1), (15, 2), (20, 5)])
def test_modifier(score, mod):
    assert checks.modifier(score) == mod


@pytest.mark.parametrize("level,bonus", [(1, 2), (4, 2), (5, 3)])
def test_proficiency(level, bonus):
    assert checks.proficiency_bonus(level) == bonus


def test_clamp_tier():
    assert checks.clamp_tier("trivial") == "easy"
    assert checks.clamp_tier("nonsense") == "medium"
    assert checks.clamp_tier("very_hard", maximum="hard") == "hard"


def test_check_success_uses_total_vs_dc():
    rng = random.Random(3)
    for _ in range(50):
        r = checks.check(rng, "stealth", 4, 13)
        assert r.success == (r.kept + 4 >= 13)


def test_levels_and_hp():
    from oathforge.content import get_content
    from oathforge.engine import class_build

    p = get_content().progression  # the XP table lives in the content now, and goes up to 20
    assert class_build.level_for_xp(0, p) == 1
    assert class_build.level_for_xp(199, p) == 1
    assert class_build.level_for_xp(200, p) == 2
    assert class_build.level_for_xp(1800, p) == 5
    assert class_build.xp_to_next(150, p) == 50
    assert class_build.xp_to_next(1800, p) == p.xp[5] - 1800
    assert progression.max_hp(10, 2, 1) == 12
    assert progression.max_hp(10, 2, 3) == 12 + 2 * 8


def test_skill_gain_diminishes():
    assert progression.skill_gain("medium", 0) == 15
    assert progression.skill_gain("medium", 1) == 7
    assert progression.skill_gain("trivial", 0) == 0
    assert progression.skill_rank(250) == 2
    assert progression.skill_rank(1000) == 3
