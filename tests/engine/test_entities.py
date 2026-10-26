"""Helpers that fight beside the hero: summons, orders, convergence, guards and forms.

Rules in planning/roadmap_balance.md §7: at most two summons, one action per round for each helper, an
order is not a second turn, a guard absorbs without a heal, a boss is never chained by an afflicting helper,
and changing shape back and forth heals nobody. The engine is pure, so all of it is tested without a database.
"""

import random

import pytest

from oathforge.content.schemas import ClassAbility, Text
from oathforge.engine import combat as cb
from oathforge.engine.combat import Action, AttackProfile, Combatant, CombatError, EncounterState, EntityTemplate, Shape

CLAW = AttackProfile(key="main", name={"es": "Garra", "en": "Claw"}, to_hit=99, damage="1d1", damage_type="slashing")


def text(s="x") -> Text:
    return Text(es=s, en=s)


def ability(kind: str, **kw) -> ClassAbility:
    return ClassAbility(name=text(), description=text(), level=1, kind=kind, **kw)


def template(key="blade", kind="summon", role="damage", **kw) -> EntityTemplate:
    base = dict(
        key=key,
        name={"es": key, "en": key},
        kind=kind,
        role=role,
        hp=10,
        to_hit=99,
        damage="1d4",
        damage_type="force",
        duration=4,
    )
    base.update(kw)
    return EntityTemplate(**base)


DEFS = {
    "call_blade": ability("summon", entity="blade"),
    "call_ember": ability("summon", entity="ember"),
    "call_guard": ability("summon", entity="guard"),
    "call_moth": ability("summon", entity="moth"),
    "order_blade": ability("command", entity="blade", extra_damage="1d4"),
    "order_guard": ability("command", entity="guard"),
    "converge": ability("converge", boost_turns=3),
    "bear": ability("shift", form="bear"),
    "panther": ability("shift", form="panther"),
    "unshift": ability("shift", form="none"),
}
TEMPLATES = {
    "blade": template("blade"),
    "ember": template("ember", role="area", damage="1d4"),
    "guard": template("guard", role="guard", hp=8, damage=None, duration=5),
    "moth": template("moth", role="disrupt", damage=None, status="frightened", period=2, duration=5),
    "servant": template("servant", kind="servant", duration=None),
    "turret": template("turret", kind="turret", duration=None, ranged=True),
    "totem": template("totem", kind="totem", role="disrupt", damage=None, status="frightened", duration=None),
}
SHAPES = {
    "bear": Shape(
        key="bear",
        name={"es": "Oso", "en": "Bear"},
        icon="🐻",
        ac_bonus=2,
        temp_hp=8,
        attacks=[
            AttackProfile(
                key="bear_0", name={"es": "Zarpazo", "en": "Claws"}, to_hit=99, damage="1d1", damage_type="slashing"
            )
        ],
    ),
    "panther": Shape(
        key="panther",
        name={"es": "Pantera", "en": "Panther"},
        icon="🐆",
        ac_bonus=0,
        temp_hp=3,
        attacks=[
            AttackProfile(
                key="panther_0", name={"es": "Mordisco", "en": "Bite"}, to_hit=99, damage="1d1", damage_type="piercing"
            )
        ],
    ),
}


def hero(**kw) -> Combatant:
    base = dict(
        id="p1",
        side="player",
        ref="1",
        name={"es": "Aldric", "en": "Aldric"},
        hp=30,
        max_hp=30,
        ac=14,
        attacks=[CLAW],
        abilities={k: None for k in DEFS},
        shapes=SHAPES,
    )
    base.update(kw)
    return Combatant(**base)


def foe(cid="m1", **kw) -> Combatant:
    base = dict(
        id=cid,
        side="enemy",
        ref="x",
        name={"es": "Bandido", "en": "Bandit"},
        hp=400,
        max_hp=400,
        ac=5,
        dex_mod=-10,
        xp=1,
        attacks=[AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=-99, damage="1d1", damage_type="slashing")],
    )
    base.update(kw)
    return Combatant(**base)


def fight(*enemies, **hero_kw) -> tuple[EncounterState, Combatant]:
    me = hero(**hero_kw)
    st = EncounterState(
        location="test", combatants={"p1": me, **{e.id: e for e in enemies}}, entity_defs=dict(TEMPLATES)
    )
    st.order = list(st.combatants)
    st.turn_index = 0
    return st, me


def act(st, key, target=None, rng=None):
    return cb.player_act(st, "p1", Action(kind="ability", ability=key, target=target), rng or random.Random(1), DEFS)


def end_turn(st, rng=None):
    return cb.player_act(st, "p1", Action(kind="end_turn"), rng or random.Random(1), DEFS)


def strikes(logs) -> list[str]:
    return [e.key for e in logs if e.key in ("combat.entity_hit", "combat.entity_crit", "combat.entity_miss")]


# ----------------------------------------------------------- summoning


def test_a_summoned_helper_waits_for_the_next_turn():
    st, me = fight(foe())
    logs = act(st, "call_blade")  # the call is the action; the turn then ends by itself
    assert [e.key for e in logs if e.key == "combat.summoned"]
    assert strikes(logs) == []  # nothing acts the turn it arrives


def test_a_helper_acts_once_at_the_end_of_each_turn():
    st, me = fight(foe())
    act(st, "call_blade")
    assert len(strikes(end_turn(st))) == 1
    assert len(strikes(end_turn(st))) == 1


def test_no_more_than_two_summons_at_once():
    st, me = fight(foe())
    act(st, "call_blade")
    me.action_used = False
    act(st, "call_ember")
    me.action_used = False
    with pytest.raises(CombatError) as err:
        act(st, "call_guard")
    assert err.value.key == "combat.err.summon_limit"
    assert len([e for e in st.entities.values() if e.active]) == 2


def test_the_same_being_is_not_called_twice_even_after_it_fell():
    """Re-summoning must never be a free heal (roadmap_balance 7.2)."""
    st, me = fight(foe())
    act(st, "call_blade")
    next(iter(st.entities.values())).defeated = True
    me.action_used = False
    with pytest.raises(CombatError) as err:
        act(st, "call_blade")
    assert err.value.key == "combat.err.already_called"


def test_a_helper_fades_when_its_time_is_up():
    st, me = fight(foe())
    act(st, "call_blade")  # duration 4
    faded = False
    for _ in range(6):
        logs = end_turn(st)
        faded = faded or any(e.key == "combat.entity_fades" for e in logs)
    assert faded and all(e.defeated for e in st.entities.values())


def test_other_kinds_are_one_each_and_permanent_ones_do_not_expire():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["servant"], persistent=True, acts_now=True)
    cb.spawn(st, me, TEMPLATES["turret"], acts_now=True)
    for _ in range(12):
        end_turn(st)
    assert all(e.active for e in st.entities.values())  # no duration, no expiry
    with pytest.raises(CombatError):
        cb._summon(st, me, ability("summon", entity="servant"))  # already there: not called again


# ------------------------------------------------------------- one action each


def test_a_bonus_action_or_a_retry_never_makes_a_helper_act_twice():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    first = cb._run_entities(st, me, random.Random(1))
    again = cb._run_entities(st, me, random.Random(1))  # the same round, asked a second time
    assert len(strikes(first)) == 1 and strikes(again) == []


def test_consulting_a_menu_or_ending_the_turn_twice_in_a_row_does_not_double_the_round():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["servant"], persistent=True, acts_now=True)  # permanent: it does not run out
    acted = []
    for _ in range(5):
        acted += strikes(end_turn(st))
    assert len(acted) == 5  # five turns, five actions: one per turn, never more


# --------------------------------------------------------------------- orders


def test_an_order_makes_it_act_now_and_not_again_as_the_turn_ends():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    logs = act(st, "order_blade")
    assert any(e.key == "combat.command" for e in logs)
    assert len(strikes(logs)) == 1  # the order was its action; the end of the turn added no second one


def test_an_order_names_the_quarry_and_the_helpers_keep_to_it():
    st, me = fight(foe("m1", hp=5), foe("m2", hp=400))
    cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    act(st, "order_blade", target="m2")
    assert me.mark == "m2"
    end_turn(st)  # next round: the blade goes for the marked one, not the weakest
    assert st.combatants["m2"].hp < 400 and st.combatants["m1"].hp == 5


def test_a_guard_takes_no_orders_and_a_missing_helper_cannot_be_ordered():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["guard"], acts_now=True)
    with pytest.raises(CombatError) as err:
        act(st, "order_guard")
    assert err.value.key == "combat.err.cannot_command"
    with pytest.raises(CombatError) as err:
        act(st, "order_blade")
    assert err.value.key == "combat.err.no_entity"


# ----------------------------------------------------------------- convergence


def test_convergence_empowers_what_is_there_and_adds_nothing():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    cb.spawn(st, me, TEMPLATES["ember"], acts_now=True)
    cb._converge(st, me, DEFS["converge"])
    assert [e.boost for e in st.entities.values()] == [3, 3]
    assert len(st.entities) == 2  # no third helper, whatever happens


def test_convergence_with_a_single_helper_boosts_that_one_only():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    cb._converge(st, me, DEFS["converge"])
    assert [e.boost for e in st.entities.values()] == [3]


def test_convergence_needs_someone_to_empower_and_refreshes_instead_of_stacking():
    st, me = fight(foe())
    with pytest.raises(CombatError) as err:
        act(st, "converge")
    assert err.value.key == "combat.err.no_entity"
    ent = cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    cb._converge(st, me, DEFS["converge"])
    ent.boost = 1
    cb._converge(st, me, DEFS["converge"])
    assert ent.boost == 3  # back to the full duration, not 4


def test_a_boosted_helper_hits_harder_and_the_boost_runs_out():
    st, me = fight(foe())
    ent = cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    cb._converge(st, me, DEFS["converge"])
    for _ in range(3):
        cb._run_entities(st, me, random.Random(2))
        st.round += 1
    assert ent.boost == 0


# --------------------------------------------------------------------- guards


def test_a_guard_takes_the_blow_in_the_heros_place():
    st, me = fight(foe())
    guard = cb.spawn(st, me, TEMPLATES["guard"], acts_now=True)
    logs = cb._apply_damage(st, me, 5, "slashing")
    assert me.hp == 30 and guard.hp == 3  # the hero took nothing
    assert [e.key for e in logs] == ["combat.guard_absorbs"]


def test_a_guard_that_breaks_lets_the_rest_through_and_does_not_come_back():
    st, me = fight(foe())
    guard = cb.spawn(st, me, TEMPLATES["guard"], acts_now=True)
    logs = cb._apply_damage(st, me, 12, "slashing")  # 8 absorbed, 4 left over
    assert guard.defeated and me.hp == 26
    assert any(e.key == "combat.entity_breaks" for e in logs)
    cb._apply_damage(st, me, 3, "slashing")
    assert me.hp == 23  # nothing left to absorb
    with pytest.raises(CombatError):
        cb._summon(st, me, ability("summon", entity="guard"))  # and it cannot be called again for a heal


# ---------------------------------------------------------- afflicting helpers


def test_an_afflicting_helper_cannot_chain_a_boss():
    boss = foe("m1", boss=True)
    st, me = fight(boss)
    cb.spawn(st, me, TEMPLATES["totem"], acts_now=True)
    for _ in range(6):
        cb._run_entities(st, me, random.Random(3))
        st.round += 1
    assert boss.statuses.get("frightened", 0) <= cb.BOSS_CONTROL_TURNS  # capped, and the rest is vulnerability


def test_the_afflicting_helper_acts_on_its_own_rhythm():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["moth"], acts_now=True)
    acted = []
    for _ in range(4):
        acted.append(any(e.key == "combat.entity_afflicts" for e in cb._run_entities(st, me, random.Random(1))))
        st.round += 1
    assert acted == [True, False, True, False]  # period 2


# ----------------------------------------------------------------- area


def test_an_area_helper_hits_the_whole_row_without_a_roll():
    a, b, c = foe("m1", row="front"), foe("m2", row="front"), foe("m3", row="back")
    st, me = fight(a, b, c)
    cb.spawn(st, me, TEMPLATES["ember"], acts_now=True)
    cb._run_entities(st, me, random.Random(1))
    assert a.hp < 400 and b.hp < 400 and c.hp == 400


# -------------------------------------------------------- owner and the end


def test_helpers_do_not_act_after_their_owner_is_down():
    st, me = fight(foe())
    cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    me.defeated = True
    st.status = "defeat"
    assert cb._run_entities(st, me, random.Random(1)) == []
    assert st.combatants["m1"].hp == 400  # and nothing was touched


def test_a_helper_can_win_the_fight():
    weak = foe(hp=1, max_hp=1, ac=1)
    st, me = fight(weak)
    cb.spawn(st, me, TEMPLATES["blade"], acts_now=True)
    end_turn(st, random.Random(5))
    assert st.status == "victory"


def test_the_whole_state_survives_being_stored_and_gives_the_same_fight():
    def play(state):
        out = []
        for _ in range(4):
            out += [e.model_dump() for e in end_turn(state, random.Random(7))]
        return out

    st, me = fight(foe())
    act(st, "call_blade")
    act_ready = EncounterState.model_validate(st.model_dump(mode="json"))  # a restart in the middle
    assert act_ready.entities.keys() == st.entities.keys()
    assert play(st) == play(act_ready)


# ------------------------------------------------------------------- shapes


def test_a_form_replaces_the_attacks_and_gives_its_reserve_once():
    st, me = fight(foe())
    act(st, "bear")
    assert me.form == "bear" and [a.key for a in me.attacks] == ["bear_0"]
    assert me.temp_hp == 8 and me.ac == 16


def test_changing_shape_back_and_forth_heals_nobody():
    st, me = fight(foe())
    act(st, "bear")
    me.temp_hp = 0  # the reserve was spent
    me.bonus_used = me.action_used = False
    act(st, "unshift")
    me.bonus_used = me.action_used = False
    act(st, "bear")
    assert me.temp_hp == 0 and me.hp == 30  # the second time round gives nothing back
    assert me.ac == 16


def test_form_to_form_swaps_the_armour_and_not_the_reserve():
    st, me = fight(foe())
    act(st, "bear")  # ac 14 + 2
    me.action_used = False
    act(st, "panther")  # the bear's armour goes, the panther's (0) comes
    assert me.form == "panther" and me.ac == 14
    assert me.temp_hp == 8  # the bigger reserve already there is not stacked with the new one


def test_leaving_the_form_gives_the_attacks_and_the_armour_back():
    st, me = fight(foe())
    act(st, "bear")
    me.action_used = False
    act(st, "unshift")
    assert me.form is None and me.attacks == [CLAW] and me.ac == 14


def test_you_cannot_take_the_form_you_have_or_leave_one_you_do_not():
    st, me = fight(foe())
    with pytest.raises(CombatError) as err:
        act(st, "unshift")
    assert err.value.key == "combat.err.no_form"
    act(st, "bear")
    me.action_used = False
    with pytest.raises(CombatError) as err:
        act(st, "bear")
    assert err.value.key == "combat.err.already_form"


def test_the_form_survives_a_restart_and_dying_in_it_is_still_dying():
    st, me = fight(foe())
    act(st, "bear")
    back = EncounterState.model_validate(st.model_dump(mode="json"))
    p = back.combatants["p1"]
    assert p.form == "bear" and p.base_attacks == [CLAW] and p.ac == 16
    cb._apply_damage(back, p, 999, "slashing")
    assert p.defeated  # no way out through the form
