"""B10: the Iron Stag (hardening, announced charge, exposed window, one more hardening), the help button's rules,
and a floor for all 41 branches at level 10 with a reasonable preparation."""

import random

import pytest

from oathforge.content import get_content
from oathforge.engine import combat as cb
from oathforge.engine import combat_help
from oathforge.engine.combat import Action
from oathforge.services import combat_service
from oathforge.tools import simulate as sim

from tests.engine.test_combat import ABILITIES, encounter, player


def stag_state(seed=0, **hero):
    st = encounter(player(hp=500, max_hp=500, ac=1, **hero), combat_service.monster_combatant("iron_stag", "m1"),
                   rng=random.Random(seed))
    return st, st.combatants["m1"]


def test_the_stag_is_a_telegraphing_boss_that_hardens_once_more_at_half_life():
    c = get_content().monsters["iron_stag"]
    assert c.boss and c.pattern.plate > 0 and c.pattern.rearm > 0 and not c.pattern.heavy.ranged
    st, stag = stag_state()
    stag.plate = 0
    log = cb._apply_damage(st, stag, stag.max_hp // 2 + 1, "slashing")
    assert "combat.plate_rearm" in [e.key for e in log]
    assert stag.plate == c.pattern.rearm and stag.rearmed
    log = cb._apply_damage(st, stag, 1, "slashing")  # a second time never happens
    stag.plate = 0
    assert "combat.plate_rearm" not in [e.key for e in cb._apply_damage(st, stag, 1, "slashing")]


def test_the_help_names_what_the_fight_asks_for_without_revealing_the_dice():
    st, stag = stag_state()
    me = st.combatants["p1"]
    assert [k for k, _ in combat_help.hints(st, me, ABILITIES)][0] == "plate"
    stag.plate, stag.pattern_state = 0, "aiming"
    assert combat_help.hints(st, me, ABILITIES)[0][0] == "aiming"
    stag.pattern_state = "reloading"
    assert combat_help.hints(st, me, ABILITIES)[0][0] == "reloading"
    stag.pattern_state = "ready"
    me.hp = 10
    assert combat_help.hints(st, me, ABILITIES)[0][0] == "low_hp"
    me.hp, stag.plate = me.max_hp, 0
    assert combat_help.hints(st, me, ABILITIES)[0][0] == "plain"  # always an answer


def test_the_help_renders_in_both_languages():
    from oathforge.bot import render
    st, stag = stag_state()
    stag.pattern_state = "aiming"
    for lang in ("es", "en"):
        text = render.combat_help_text(st, st.combatants["p1"], ABILITIES, lang)
        assert text and "{" not in text and len(text) < 600


@pytest.mark.parametrize("branch", sorted(get_content().class_specializations))
def test_every_branch_can_beat_the_stag_at_level_ten_with_a_reasonable_preparation(branch):
    cls = get_content().class_specializations[branch].class_key
    rows = sim.simulate([cls], ["iron_stag"], [10], n=20, seed=3, lineage="human", background="soldier", branch=branch)
    assert rows[0]["win_pct"] >= 20, rows[0]
