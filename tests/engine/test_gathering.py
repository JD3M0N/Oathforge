import random

from oathforge.content import get_content
from oathforge.engine import gathering


def mine():
    return next(g for g in get_content().locations["ironvein_mine"].gathering if g.skill == "mining")


def test_rank_curve():
    assert [gathering.rank_for(x) for x in (0, 79, 80, 239, 240, 500, 899, 900, 1499, 1500, 99999)] == [
        0,
        0,
        1,
        1,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
    ]
    assert gathering.next_threshold(0) == 80 and gathering.next_threshold(1500) is None


def test_bonus_chance_is_capped():
    assert gathering.bonus_chance(0) == 0
    assert gathering.bonus_chance(5) == gathering.BONUS_CAP == 0.20


def test_gather_and_stay_amounts():
    for seed in range(200):
        quick = gathering.roll_gather(random.Random(seed), mine().resources, 0, "gather")
        assert 2 <= sum(quick.items.values()) <= 3 and quick.xp == 10 and not quick.bonus  # rank 0: no bonus
        stay = gathering.roll_gather(random.Random(seed), mine().resources, 5, "stay")
        assert 8 <= sum(stay.items.values()) <= 10 and 25 <= stay.xp <= 30
        assert sum(stay.bonus.values()) <= gathering.BONUS_ROLLS["stay"]


def test_rare_resources_need_rank():
    found_low = set()
    found_high = set()
    for seed in range(300):
        found_low |= set(gathering.roll_gather(random.Random(seed), mine().resources, 0, "stay").items)
        found_high |= set(gathering.roll_gather(random.Random(seed), mine().resources, 3, "stay").items)
    assert found_low == {"iron_ore", "coal"}
    assert {"copper_ore", "rough_gem"} <= found_high


def test_bonus_is_about_a_fifth_at_top_rank():
    hits = sum(bool(gathering.roll_gather(random.Random(s), mine().resources, 5, "gather").bonus) for s in range(2000))
    assert 0.15 < hits / 2000 < 0.25


def test_half_and_harvest():
    assert gathering.half({"iron_ore": 9, "coal": 1}) == {"iron_ore": 4}
    boar = get_content().monsters["boar"].harvest
    always = gathering.roll_harvest(random.Random(0), get_content().monsters["old_tusk"].harvest, 0)
    assert always == {"boar_hide": 2, "raw_meat": 4}
    assert set(gathering.roll_harvest(random.Random(1), boar, 5)) <= {"boar_hide", "raw_meat"}
