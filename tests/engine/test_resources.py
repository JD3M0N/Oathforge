"""The class's own bar: what it pays, what it puts back and what it refuses.

Rules in planning/roadmap_balance.md §5.1 and §5.3. The basic attack is always free and always
useful, a cooldown is counted in turns of combat and a boss is never chained by hard control.
"""

import random

import pytest

from oathforge.content import get_content
from oathforge.engine import combat as cb
from oathforge.engine.combat import Action, AttackProfile, Combatant, CombatError, EncounterState

SWORD = AttackProfile(key="main", name={"es": "Espada", "en": "Sword"}, to_hit=99, damage="1d1", damage_type="slashing")
ABILITIES = {k: a for cls in get_content().classes.values() for k, a in cls.abilities.items()}


def hero(**kw) -> Combatant:
    base = dict(
        id="p1",
        side="player",
        ref="1",
        name={"es": "Aldric", "en": "Aldric"},
        hp=20,
        max_hp=20,
        ac=16,
        attacks=[SWORD],
        resource=5,
        resource_max=10,
        resource_key="focus",
    )
    base.update(kw)
    return Combatant(**base)


def dummy(cid="m1", **kw) -> Combatant:
    base = dict(
        id=cid,
        side="enemy",
        ref="bandit",
        name={"es": "Bandido", "en": "Bandit"},
        hp=500,
        max_hp=500,
        ac=99,
        dex_mod=-10,  # it never hits back and never dies: the test is about the bar
        attacks=[AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=-99, damage="1d1", damage_type="slashing")],
        xp=1,
    )
    base.update(kw)
    return Combatant(**base)


def encounter(*cs) -> EncounterState:
    st = EncounterState(location="test", combatants={c.id: c for c in cs})
    st.order = [c.id for c in cs]
    st.turn_index = 0
    return st


def act(st, action, rng=None):
    return cb.player_act(st, "p1", action, rng or random.Random(0), ABILITIES)


# ------------------------------------------------------------- paying for it


def test_a_power_costs_once_and_only_once():
    me = hero(abilities={"second_wind": None}, hp=5)
    st = encounter(me, dummy())
    act(st, Action(kind="ability", ability="second_wind"))
    assert me.resource == 5 - ABILITIES["second_wind"].cost
    assert [e.key for e in st.log if e.key == "combat.resource_spent"] == ["combat.resource_spent"]


def test_without_enough_in_the_bar_it_is_refused_and_nothing_is_spent():
    me = hero(abilities={"second_wind": None}, resource=1, hp=5)
    st = encounter(me, dummy())
    with pytest.raises(CombatError) as err:
        act(st, Action(kind="ability", ability="second_wind"))
    assert err.value.key == "combat.err.no_resource"
    assert me.resource == 1 and me.hp == 5 and not me.bonus_used  # the turn is untouched


def test_the_basic_attack_is_free_and_feeds_the_bar():
    me = hero(resource=0, resource_on_attack=2)
    st = encounter(me, dummy())
    act(st, Action(kind="attack", weapon="main"))
    assert me.resource == 2
    assert [e.key for e in st.log if e.key == "combat.resource_gained"] == ["combat.resource_gained"]


def test_an_extra_attack_does_not_feed_the_bar_twice():
    """Two swings are one action: the bar grows once per action, never per swing."""
    me = hero(resource=0, resource_on_attack=2, extra_attack=True)
    st = encounter(me, dummy())
    act(st, Action(kind="attack", weapon="main"))
    assert me.resource == 2


def test_the_bar_never_goes_over_its_maximum():
    me = hero(resource=9, resource_max=10, resource_on_attack=5)
    st = encounter(me, dummy())
    act(st, Action(kind="attack", weapon="main"))
    assert me.resource == 10


def test_a_class_without_a_bar_keeps_paying_with_uses():
    me = hero(abilities={"lay_on_hands": 1}, resource=0, resource_max=0, hp=5)
    st = encounter(me, dummy())
    act(st, Action(kind="ability", ability="lay_on_hands"))
    assert me.abilities["lay_on_hands"] == 0 and me.resource == 0
    me.bonus_used = False  # a fresh turn: what stops it now is the spent use, not the bonus action
    with pytest.raises(CombatError) as err:
        act(st, Action(kind="ability", ability="lay_on_hands"))
    assert err.value.key == "combat.err.no_uses"


# ---------------------------------------------------------------- cooldowns


def test_a_cooldown_is_counted_in_turns_and_blocks_meanwhile():
    me = hero(abilities={"second_wind": None}, resource=10, hp=1)
    st = encounter(me, dummy())
    act(st, Action(kind="ability", ability="second_wind"))
    assert me.cooldowns["second_wind"] == ABILITIES["second_wind"].cooldown
    me.hp, me.bonus_used = 1, False  # a fresh turn: what stops it is the cooldown
    with pytest.raises(CombatError) as err:
        act(st, Action(kind="ability", ability="second_wind"))
    assert err.value.key == "combat.err.cooldown"


def test_the_cooldown_runs_down_on_its_owner_turn_and_the_power_comes_back():
    me = hero(abilities={"second_wind": None}, resource=10, hp=1)
    st = encounter(me, dummy())
    act(st, Action(kind="ability", ability="second_wind"))
    cd = ABILITIES["second_wind"].cooldown
    for _ in range(cd):
        assert me.cooldowns.get("second_wind", 0) > 0
        act(st, Action(kind="end_turn"))
    assert not me.cooldowns.get("second_wind")
    me.hp = 1
    act(st, Action(kind="ability", ability="second_wind"))  # usable again, no exception
    assert me.hp > 1


def test_a_power_you_cannot_pay_for_is_not_offered():
    me = hero(abilities={"second_wind": None}, resource=0, hp=1)
    st = encounter(me, dummy())
    assert cb.available_bonus_actions(st, me, ABILITIES) == []
    me.resource = 10
    assert cb.available_bonus_actions(st, me, ABILITIES) == ["second_wind"]
    me.cooldowns = {"second_wind": 1}
    assert cb.available_bonus_actions(st, me, ABILITIES) == []


# ----------------------------------------------------------- turn and regen


def test_the_bar_fills_a_little_at_the_start_of_its_own_turn():
    me = hero(resource=0, resource_per_turn=2)
    st = encounter(me, dummy())
    act(st, Action(kind="end_turn"))  # the dummy plays and the turn comes back round
    assert me.resource == 2


def test_the_bar_survives_being_stored_and_read_back():
    me = hero(resource=7, cooldowns={"second_wind": 2})
    st = encounter(me, dummy())
    back = EncounterState.model_validate(st.model_dump(mode="json"))
    p = back.combatants["p1"]
    assert (p.resource, p.resource_max, p.resource_key) == (7, 10, "focus")
    assert p.cooldowns == {"second_wind": 2}


# --------------------------------------------------------------- boss control


def test_hard_control_does_not_chain_a_boss_and_says_so():
    boss = dummy(boss=True)
    st = encounter(hero(), boss)
    logs = cb._apply_status(boss, "stunned", 3)
    assert boss.statuses["stunned"] == cb.BOSS_CONTROL_TURNS
    assert boss.statuses["vulnerable"] == 3 - cb.BOSS_CONTROL_TURNS  # what was cut is not lost
    assert [e.key for e in logs] == ["combat.boss_resists", "combat.status"]


def test_a_boss_takes_the_soft_statuses_whole():
    boss = dummy(boss=True)
    logs = cb._apply_status(boss, "burning", 4)
    assert boss.statuses["burning"] == 4 and "vulnerable" not in boss.statuses
    assert [e.key for e in logs] == ["combat.status"]


def test_an_ordinary_enemy_is_controlled_for_the_whole_duration():
    foe = dummy()
    cb._apply_status(foe, "stunned", 3)
    assert foe.statuses["stunned"] == 3 and "vulnerable" not in foe.statuses


def test_a_status_refreshes_and_never_stacks():
    foe = dummy()
    cb._apply_status(foe, "burning", 2)
    cb._apply_status(foe, "burning", 1)
    assert foe.statuses["burning"] == 2  # the longer one wins; they do not add up
    cb._apply_status(foe, "burning", 5)
    assert foe.statuses["burning"] == 5


# ---------------------------------------------- the acceptance case of B03


@pytest.mark.parametrize("class_key,level", [("warrior", 1), ("warrior", 5), ("sorcerer", 3), ("sorcerer", 5)])
def test_a_focus_fighter_and_a_mana_caster_get_through_several_fights(class_key, level):
    """roadmap_balance B03: several fights in a row without a broken economy. The bar runs down and
    comes back by its own rules, nobody is ever left with nothing useful to do, and nothing goes
    negative or over the top."""
    from oathforge.tools import simulate as sim

    me, defs = sim.hero(class_key, level, "human", "soldier")
    assert me.resource_max > 0, f"{class_key} should have its own bar"
    seen_spent = False
    for fight in range(4):
        # a foe that really hits back: otherwise a level-1 warrior never needs its heal
        foe = Combatant(
            id=f"m{fight}",
            side="enemy",
            ref="bandit",
            name={"es": "Bandido", "en": "Bandit"},
            hp=22,
            max_hp=22,
            ac=11,
            dex_mod=-10,
            xp=1,
            attacks=[
                AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=6, damage="1d6+2", damage_type="slashing")
            ],
        )
        st = EncounterState(location="test", combatants={"p1": me, foe.id: foe})
        cb.start(st, random.Random(fight))
        # fights in a row, with no full rest in between: this is what wears the bar down
        me.hp, start = max(1, me.max_hp // 2), me.resource
        for _ in range(12):
            if st.status != "active" or st.current.id != "p1":
                break
            sim.play_turn(st, random.Random(fight), defs)
            assert 0 <= me.resource <= me.resource_max, "the bar went out of its own range"
        seen_spent = seen_spent or me.resource < start
        # whatever is left in the bar, there is always a free attack to make
        assert me.attacks and all(a.damage for a in me.attacks)
    assert seen_spent, f"{class_key} never spent its bar in four fights"
