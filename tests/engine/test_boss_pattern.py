"""A boss with a pattern (roadmap_balance §9.1): plate, signalled heavy attack, reload window."""

import random

from oathforge.engine import combat as cb
from oathforge.engine.combat import Action, AttackProfile

from tests.engine.test_combat import ABILITIES, encounter, monster, player

HEAVY = AttackProfile(key="heavy", name={"es": "Descarga", "en": "Volley"}, to_hit=30, damage="1d4", damage_type="piercing",
                      ranged=True)


def boss(**kw):
    base = dict(hp=60, max_hp=60, plate=10, plate_max=10, pattern={"cycle": 2, "cycle_broken": 1}, heavy=HEAVY, boss=True)
    base.update(kw)
    return monster("m1", **base)


def keys(logs):
    return [e.key for e in logs]


def pass_turn(st, rng):
    return cb.player_act(st, "p1", Action(kind="defend"), rng, ABILITIES) and st.log


def test_the_boss_aims_out_loud_fires_and_then_reloads_exposed():
    rng = random.Random(1)
    st = encounter(player(hp=500, max_hp=500, ac=1), boss(), rng=rng)
    seen = []
    for _ in range(8):
        logs = cb.player_act(st, "p1", Action(kind="defend"), rng, ABILITIES)
        seen += keys(logs)
        if st.status != "active":
            break
    order = [k for k in seen if k in ("combat.boss_aim", "combat.boss_fire", "combat.boss_reload")]
    assert order[:3] == ["combat.boss_aim", "combat.boss_fire", "combat.boss_reload"]  # aim, then fire, then reload
    assert order.index("combat.boss_aim") < order.index("combat.boss_fire") < order.index("combat.boss_reload")


def test_the_fired_boss_is_exposed_for_the_heros_next_turn():
    rng = random.Random(2)
    st = encounter(player(hp=500, max_hp=500, ac=1), boss(), rng=rng)
    for _ in range(8):
        cb.player_act(st, "p1", Action(kind="defend"), rng, ABILITIES)
        if st.combatants["m1"].pattern_state == "reloading":
            break
    assert st.combatants["m1"].pattern_state == "reloading"
    assert "vulnerable" in st.combatants["m1"].statuses  # the hero's turn: hits land harder


def test_damage_wears_the_plate_before_the_hp_and_speeds_the_boss_up():
    rng = random.Random(3)
    b = boss(plate=5, plate_max=5)
    st = encounter(player(hp=500, max_hp=500, ac=1), b, rng=rng)
    log = cb._apply_damage(st, st.combatants["m1"], 3, "slashing")
    assert keys(log) == ["combat.plate_hit"] and st.combatants["m1"].plate == 2 and st.combatants["m1"].hp == 60
    log = cb._apply_damage(st, st.combatants["m1"], 6, "slashing")
    assert "combat.plate_broken" in keys(log) and st.combatants["m1"].plate == 0
    assert st.combatants["m1"].hp == 60 - 4  # what the plate could not take goes through


def test_a_plain_monster_has_no_plate_and_no_pattern():
    st = encounter(player(), monster("m1"), rng=random.Random(0))
    log = cb._apply_damage(st, st.combatants["m1"], 3, "slashing")
    assert "combat.plate_hit" not in keys(log) and st.combatants["m1"].pattern is None
