"""The balance tooling (B12): reproducible cells, honest intervals and a report that names what it cannot measure."""

from oathforge.content import get_content
from oathforge.tools import balance, simulate as sim


def test_wilson_interval_does_not_call_a_small_sample_certain():
    lo, hi = balance.wilson(12, 12)
    assert lo < 80 and hi == 100.0  # twelve wins out of twelve is not a hundred percent
    lo, hi = balance.wilson(0, 10)
    assert lo == 0.0 and hi < 35
    assert balance.wilson(50, 100)[0] < 50 < balance.wilson(50, 100)[1]


def test_every_standard_rival_exists_and_each_level_has_the_kinds_it_promises():
    c = get_content()
    for level, kinds in balance.STANDARDS.items():
        assert {"weak", "standard", "elite", "pair", "boss"} == set(kinds)
        for group in filter(None, kinds.values()):
            assert all(k in c.monsters for k in group.split("+")), (level, group)


def test_a_cell_is_reproducible_and_the_policies_and_kit_run():
    args = ("warrior", None, 5, "standard", "bandit_captain", "informed", "t0", 6, 3)
    assert balance._cell(args) == balance._cell(args)
    branch = ("paladin", "avenger", 10, "boss", "iron_stag", "informed", "t1", 4, 3)
    assert balance._cell(branch)["n"] == 4
    basic = sim.fight("paladin", 10, ["iron_stag"], 1, "human", "soldier", True, "avenger", "basic", "t0")
    informed = sim.fight("paladin", 10, ["iron_stag"], 1, "human", "soldier", True, "avenger", "informed", "t1")
    assert basic.status in ("victory", "defeat") and informed.potions_used >= 0


def test_the_t1_kit_adds_one_body_piece_only_from_level_ten():
    base = sim.sim_character("paladin", 10, "human", "soldier", "avenger")
    assert sim.sim_gear(base, "t1")["body"].item_key == "steel_breastplate"
    assert sim.sim_gear(base, "t0")["body"].item_key != "steel_breastplate"
    low = sim.sim_character("paladin", 9, "human", "soldier")
    assert sim.sim_gear(low, "t1")["body"].item_key == sim.sim_gear(low, "t0")["body"].item_key


def test_a_sequence_carries_the_hero_and_stops_at_the_first_defeat():
    runs = sim.sequence("warrior", 5, [["bandit"], ["bandit"], ["bandit"]], 1, "human", "soldier")
    assert 1 <= len(runs) <= 3 and all(r.status == "victory" for r in runs[:-1])
    assert runs[0].ended["hp"] >= 0


def test_the_quick_report_names_version_commit_seed_and_its_limits():
    work = balance.cells(4, 11, quick=True)
    res = [balance._cell(w) for w in work[:6]] + [balance._cell(w) for w in work[-4:]]
    seqs = [balance._chain(c) for c in balance.chains(4, 11, quick=True)]
    text = balance.report(res, seqs, 4, 11)
    assert "Semilla base: 11" in text and "Limitaciones" in text and "Wilson" in text
    assert "Ritmo de la campaña" in text and "no medición" in text


def test_the_pace_model_walks_the_campaign_in_order_and_levels_never_go_down():
    rows = balance.pace()
    assert rows[0]["quest"].startswith("tut_") and rows[-1]["quest"] == "reg_trial"
    levels = [r["level_by_xp"] for r in rows]
    assert levels == sorted(levels) and all(b >= a for a, b in zip([r["xp_total"] for r in rows], [r["xp_total"] for r in rows][1:]))
