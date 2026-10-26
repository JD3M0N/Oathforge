"""The shared mechanics the 41 branches are built from (B07): spend a status, strike back, leech, cut cooldowns.

Each one is tested alone here; test_branches.py then checks that every branch uses them as designed.
"""

import random

import pytest

from oathforge.content.schemas import AbilityPatch, ClassAbility, Text
from oathforge.engine import class_build
from oathforge.engine import combat as cb
from oathforge.engine.combat import Action, AttackProfile, Combatant, EncounterState

T = Text(es="x", en="x")
SWORD = AttackProfile(key="main", name={"es": "E", "en": "S"}, to_hit=99, damage="1d1", damage_type="slashing")
HIT_BACK = AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=99, damage="1d4", damage_type="slashing")
HARMLESS = HIT_BACK.model_copy(update={"to_hit": -99})


def ab(kind="strike", **kw) -> ClassAbility:
    return ClassAbility(name=T, description=T, level=10, kind=kind, **kw)


def hero(**kw) -> Combatant:
    base = dict(
        id="p1",
        side="player",
        ref="1",
        name={"es": "H", "en": "H"},
        hp=30,
        max_hp=30,
        ac=1,
        attacks=[SWORD],
        resource=20,
        resource_max=20,
        resource_key="focus",
    )
    base.update(kw)
    return Combatant(**base)


def foe(**kw) -> Combatant:
    """It never hits back unless a test gives it a real attack: otherwise the end of the turn muddies the figures."""
    base = dict(
        id="m1",
        side="enemy",
        ref="x",
        name={"es": "x", "en": "x"},
        hp=300,
        max_hp=300,
        ac=1,
        dex_mod=-10,
        xp=1,
        attacks=[HARMLESS],
    )
    base.update(kw)
    return Combatant(**base)


def fight(me, *enemies) -> EncounterState:
    st = EncounterState(location="t", combatants={"p1": me, **{e.id: e for e in enemies}})
    st.order, st.turn_index = list(st.combatants), 0
    return st


def use(st, defs, key, target="m1", seed=3):
    return cb.player_act(st, "p1", Action(kind="ability", ability=key, target=target), random.Random(seed), defs)


def keys(logs):
    return [e.key for e in logs]


# ------------------------------------------------------------------ spend a status


def test_a_strike_spends_the_status_it_finds_and_hurts_more():
    defs = {"smite": ab(extra_damage="1d1", damage_type="radiant", consumes="marked", consume_damage="10d1")}
    me, target = hero(abilities={"smite": None}), foe()
    st = fight(me, target)
    cb._apply_status(target, "marked", 5)
    logs = use(st, defs, "smite")
    assert "combat.consumed" in keys(logs) and "marked" not in target.statuses
    assert 300 - target.hp >= 10  # the ten from the mark that was spent, on top of the blow


def test_without_the_status_it_is_only_what_it_is():
    defs = {"smite": ab(extra_damage="1d1", damage_type="radiant", consumes="marked", consume_damage="10d1")}
    me, target = hero(abilities={"smite": None}), foe()
    st = fight(me, target)
    logs = use(st, defs, "smite")
    assert "combat.consumed" not in keys(logs) and 300 - target.hp < 10


def test_a_spell_and_a_save_can_spend_a_status_too():
    defs = {
        "burst": ab("spell", damage="1d1", damage_type="fire", auto_hit=True, consumes="burning", consume_damage="8d1"),
        "wave": ab("save", damage="1d1", damage_type="cold", save="dex", consumes="restrained", consume_damage="8d1"),
    }
    me = hero(abilities={"burst": None, "wave": None})
    target = foe()
    st = fight(me, target)
    cb._apply_status(target, "burning", 3)
    assert "combat.consumed" in keys(use(st, defs, "burst")) and "burning" not in target.statuses
    me.action_used = False
    cb._apply_status(target, "restrained", 3)
    assert "combat.consumed" in keys(use(st, defs, "wave")) and "restrained" not in target.statuses


# ------------------------------------------------------------------------ leech


def test_a_leech_heals_a_share_of_the_real_damage_and_no_more():
    defs = {"drain": ab(extra_damage="9d1", damage_type="necrotic", leech_pct=50)}
    me, target = hero(abilities={"drain": None}, hp=10), foe()
    st = fight(me, target)
    logs = use(st, defs, "drain")
    dealt = 300 - target.hp
    healed = me.hp - (10 - 0)  # nothing hit the hero: the whole change is the leech
    assert healed == dealt * 50 // 100 and "combat.leech" in keys(logs)


def test_a_leech_never_heals_past_the_maximum_and_never_on_a_miss():
    defs = {"drain": ab(extra_damage="9d1", damage_type="necrotic", leech_pct=100)}
    me, target = hero(abilities={"drain": None}, hp=29), foe()
    st = fight(me, target)
    use(st, defs, "drain")
    assert me.hp <= me.max_hp
    me2, target2 = hero(abilities={"drain": None}, hp=5, attacks=[SWORD.model_copy(update={"to_hit": -99})]), foe()
    st2 = fight(me2, target2)
    use(st2, defs, "drain")
    assert me2.hp == 5  # nothing landed, nothing healed


# --------------------------------------------------------------------- thorns


def test_a_hurt_hero_with_thorns_hits_back_once_per_attack():
    me = hero(thorns="6d1", thorns_type="radiant", ac=1)
    attacker = foe(attacks=[HIT_BACK])
    st = fight(me, attacker)
    logs = cb._attack(st, attacker, me, attacker.attacks[0], random.Random(1), None)
    assert keys(logs).count("combat.thorns") == 1 and attacker.hp <= 300 - 6


def test_thorns_need_a_real_wound_and_a_miss_answers_nothing():
    me = hero(thorns="6d1", ac=999)  # nothing gets through
    attacker = foe(attacks=[HIT_BACK])
    st = fight(me, attacker)
    logs = cb._attack(st, attacker, me, attacker.attacks[0], random.Random(1), None)
    assert "combat.thorns" not in keys(logs) and attacker.hp == 300


def test_thorns_never_answer_themselves():
    a, b = hero(thorns="3d1", ac=1), foe(thorns="3d1", attacks=[HIT_BACK])  # an enemy with the very same trait
    st = fight(a, b)
    b.side = "enemy"
    logs = cb._attack(st, b, a, b.attacks[0], random.Random(2), None)
    assert keys(logs).count("combat.thorns") == 1  # one answer, and it does not bounce back and forth


def test_being_hurt_fills_the_bar_up_to_its_top():
    me = hero(resource=0, resource_max=3, resource_on_hurt=2, ac=1)
    attacker = foe(attacks=[HIT_BACK])
    st = fight(me, attacker)
    cb._attack(st, attacker, me, attacker.attacks[0], random.Random(1), None)
    assert me.resource == 2
    cb._attack(st, attacker, me, attacker.attacks[0], random.Random(2), None)
    assert me.resource == 3  # capped


# ------------------------------------------------------------------- cooldowns


def test_cutting_cooldowns_takes_turns_off_the_others_but_not_itself():
    defs = {"rewind": ab("buff", reduces_cooldowns=2, cooldown=4)}
    me = hero(abilities={"rewind": None, "big": None}, cooldowns={"big": 3, "small": 1})
    st = fight(me, foe())
    logs = cb._use_ability(st, me, Action(kind="ability", ability="rewind"), defs["rewind"], random.Random(1))
    assert me.cooldowns == {"big": 1, "rewind": 4}  # the small one is ready, the big one shortened, itself intact
    assert "combat.cooldowns_cut" in keys(logs)


# ----------------------------------------------------------------------- heal


def test_a_heal_that_really_heals_leaves_a_barrier():
    defs = {"mend": ab("heal", heal_dice="5d1", temp_hp="4d1")}
    me = hero(abilities={"mend": None}, hp=10)
    st = fight(me, foe())
    use(st, defs, "mend")
    assert me.hp >= 15 and me.temp_hp >= 4


def test_a_heal_at_full_life_is_refused_so_it_cannot_farm_barriers():
    defs = {"mend": ab("heal", heal_dice="5d1", temp_hp="4d1")}
    me = hero(abilities={"mend": None}, hp=30)
    st = fight(me, foe())
    with pytest.raises(cb.CombatError):
        use(st, defs, "mend")
    assert me.temp_hp == 0


# ---------------------------------------------------------------------- patches


def test_a_patch_replaces_dice_only_where_there_are_dice():
    base = ab(extra_damage="1d8", consumes="marked", consume_damage="2d8")
    out = class_build._patched(base, AbilityPatch(extra_damage="2d8", consume_damage="5d8", heal_dice="9d9"))
    assert (out.extra_damage, out.consume_damage, out.heal_dice) == ("2d8", "5d8", None)  # no heal to replace


def test_a_patch_changes_a_leech_only_if_the_ability_leeches():
    assert class_build._patched(ab(leech_pct=30), AbilityPatch(leech_pct=60)).leech_pct == 60
    assert class_build._patched(ab(), AbilityPatch(leech_pct=60)).leech_pct == 0
