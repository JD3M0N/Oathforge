"""The rare find and the tool bonuses: one roll per activity, relative percentages, same economy."""

import random

from oathforge.content import get_content
from oathforge.engine import gathering

MINE = "ironvein_mine"


def resources(location=MINE):
    return get_content().locations[location].gathering[0].resources


def test_a_rare_find_is_one_roll_for_the_whole_activity():
    res = resources()
    assert gathering.rare_chance(res, 0, "gather") == 0  # no rare is within reach yet
    base = gathering.rare_chance(res, 3, "gather")
    assert 0 < base < 1
    # +5 % is relative, not five points: 10 % becomes 10.5 %, never 15 %
    with_tool = gathering.rare_chance(res, 3, "gather", gathering.Mods(rare_rel=0.05))
    assert abs(with_tool - base * 1.05) < 1e-9
    # and no pile of bonuses ever makes it certain
    assert gathering.rare_chance(res, 3, "stay", gathering.Mods(rare_rel=10)) <= gathering.RARE_CAP


def test_at_most_one_rare_per_activity_and_it_replaces_a_common_unit():
    res = resources()
    rng = random.Random(3)
    sizes, rares = set(), 0
    for _ in range(400):
        roll = gathering.roll_gather(rng, res, 5, "gather", gathering.Mods(rare_rel=10))
        got = roll.items
        sizes.add(sum(got.values()))
        rares += got.get("rough_gem", 0)
        assert got.get("rough_gem", 0) <= 1  # one find, not a handful
    assert sizes <= set(range(*gathering.GATHER_UNITS)) | {gathering.GATHER_UNITS[1]}  # the count did not grow
    assert rares > 0


def test_the_extra_unit_is_rolled_once_per_activity():
    res = resources()
    rng = random.Random(4)
    always = gathering.Mods(extra_chance=1.0)
    for _ in range(50):
        roll = gathering.roll_gather(rng, res, 0, "gather", always)
        assert sum(roll.bonus.values()) == 1  # exactly one extra, however many units came out
        assert roll.xp == gathering.GATHER_XP  # and the extra pays no XP


def test_a_faster_tool_shortens_the_wait_without_going_under_the_floor():
    assert gathering.Mods(time_pct=0.10).seconds(300) == 270
    assert gathering.Mods().seconds(300) == 300
    assert gathering.Mods(time_pct=0.99).seconds(300) == gathering.MIN_SECONDS


def test_the_new_rolls_keep_the_old_economy():
    """Splitting the rare find out must not quietly change what an hour of mining is worth."""
    res = resources()
    rng = random.Random(11)
    totals: dict[str, int] = {}
    runs = 4000
    for _ in range(runs):
        for item, qty in gathering.roll_gather(rng, res, 5, "gather").total().items():
            totals[item] = totals.get(item, 0) + qty
    per_run = {k: v / runs for k, v in totals.items()}
    assert 2.0 < sum(per_run.values()) < 3.5  # still two or three units, plus the rank bonus
    assert 0.03 < per_run["rough_gem"] < 0.15  # the rare one stays rare, in the same order of magnitude
