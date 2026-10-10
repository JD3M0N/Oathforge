import random

import pytest

from oathforge.content import get_content
from oathforge.engine import combat as cb
from oathforge.engine.combat import Action, AttackProfile, Combatant, CombatError, EncounterState

ABILITIES = get_content().classes["paladin"].abilities | get_content().classes["rogue"].abilities
SWORD = AttackProfile(key="main", name={"es": "Espada", "en": "Sword"}, to_hit=5, damage="1d8+3", damage_type="slashing")
BOW = AttackProfile(key="ranged", name={"es": "Arco", "en": "Bow"}, to_hit=5, damage="1d6+3", damage_type="piercing", ranged=True)
DAGGER = AttackProfile(key="main", name={"es": "Daga", "en": "Dagger"}, to_hit=5, damage="1d4+3", damage_type="piercing", finesse=True)


def player(**kw) -> Combatant:
    base = dict(id="p1", side="player", ref="1", name={"es": "Aldric", "en": "Aldric"}, hp=20, max_hp=20, ac=16,
                dex_mod=0, attacks=[SWORD], skill_bonus={"athletics": 5, "stealth": 5})
    base.update(kw)
    return Combatant(**base)


def monster(cid="m1", **kw) -> Combatant:
    base = dict(id=cid, side="enemy", ref="bandit", name={"es": "Bandido", "en": "Bandit"}, hp=11, max_hp=11, ac=12,
                dex_mod=1, attacks=[AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=3, damage="1d6+1",
                                                  damage_type="slashing")], xp=25)
    base.update(kw)
    return Combatant(**base)


def encounter(*cs, rng=None) -> EncounterState:
    st = EncounterState(location="test", combatants={c.id: c for c in cs})
    cb.start(st, rng or random.Random(0))
    return st


def play_until_done(st, rng, max_steps=200):
    steps = 0
    while st.status == "active" and steps < max_steps:
        steps += 1
        target = cb.melee_targets(st, st.current)[0].id
        cb.player_act(st, st.current.id, Action(kind="attack", weapon="main", target=target), rng, ABILITIES)
    return steps


def test_initiative_orders_everyone_and_player_acts_first_turn():
    st = encounter(player(), monster("m1"), monster("m2"))
    assert sorted(st.order) == ["m1", "m2", "p1"]
    assert st.status == "active" and st.current.id == "p1"
    inits = [st.combatants[c].initiative for c in st.order]
    assert inits == sorted(inits, reverse=True)


def test_fight_terminates_deterministically():
    results = set()
    for seed in range(5):
        rng = random.Random(seed)
        st = encounter(player(), monster(), rng=rng)
        play_until_done(st, rng)
        assert st.status in ("victory", "defeat")
        results.add(st.status)
    assert "victory" in results


def test_same_seed_same_outcome():
    def run():
        rng = random.Random(42)
        st = encounter(player(), monster("m1"), monster("m2"), rng=rng)
        play_until_done(st, rng)
        return st.model_dump()
    assert run() == run()


def test_not_your_turn_rejected():
    st = encounter(player(), monster())
    with pytest.raises(CombatError) as e:
        cb.player_act(st, "m1", Action(kind="defend"), random.Random(0), ABILITIES)
    assert e.value.key == "combat.err.not_your_turn"


def test_bad_target_rejected():
    st = encounter(player(), monster())
    with pytest.raises(CombatError):
        cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="nope"), random.Random(0), ABILITIES)


def test_melee_must_hit_front_row_first():
    front, back = monster("m1"), monster("m2", row="back")
    st = encounter(player(), front, back)
    with pytest.raises(CombatError):
        cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m2"), random.Random(0), ABILITIES)


def test_ranged_can_target_back_row():
    st = encounter(player(attacks=[SWORD, BOW]), monster("m1"), monster("m2", row="back"))
    cb.player_act(st, "p1", Action(kind="attack", weapon="ranged", target="m2"), random.Random(0), ABILITIES)


def test_ability_uses_are_consumed():
    rng = random.Random(5)
    st = encounter(player(abilities={"consecrated_strike": 1}), monster(hp=200, max_hp=200), rng=rng)
    cb.player_act(st, "p1", Action(kind="ability", ability="consecrated_strike", target="m1"), rng, ABILITIES)
    assert st.combatants["p1"].abilities["consecrated_strike"] == 0
    if st.status == "active":
        with pytest.raises(CombatError):
            cb.player_act(st, "p1", Action(kind="ability", ability="consecrated_strike", target="m1"), rng, ABILITIES)


def test_bonus_action_heal_keeps_turn():
    st = encounter(player(hp=5, abilities={"lay_on_hands": 1}), monster())
    cb.player_act(st, "p1", Action(kind="ability", ability="lay_on_hands"), random.Random(0), ABILITIES)
    p = st.combatants["p1"]
    assert p.hp == 10 and p.bonus_used and not p.action_used and st.current.id == "p1"


def test_defend_imposes_disadvantage_until_next_turn():
    st = encounter(player(), monster())
    st.combatants["p1"].statuses["defending"] = 1
    st.combatants["p1"].action_used = True
    entry = None
    for e in cb.player_act(st, "p1", Action(kind="end_turn"), random.Random(1), ABILITIES):
        if e.key in ("combat.hit", "combat.miss", "combat.crit") and e.params["actor"] == "m1":
            entry = e
    assert entry is not None and entry.params["dis"] is True
    assert "defending" not in st.combatants["p1"].statuses  # cleared at start of own turn


def test_stunned_skips_turn_and_dot_ticks():
    st = encounter(player(), monster(hp=100, max_hp=100))
    st.combatants["m1"].statuses.update({"stunned": 1, "bleeding": 2})
    logs = cb.player_act(st, "p1", Action(kind="defend"), random.Random(0), ABILITIES)
    keys = [e.key for e in logs]
    assert "combat.stunned" in keys and "combat.dot" in keys
    assert "stunned" not in st.combatants["m1"].statuses


def test_immunity_blocks_status():
    m = monster(immune=["bleeding"])
    logs = cb._apply_status(m, "bleeding", 2)
    assert logs[0].key == "combat.immune" and "bleeding" not in m.statuses


def test_relentless_once():
    p = player(hp=3, relentless=True)
    st = EncounterState(location="t", combatants={"p1": p})
    cb._apply_damage(st, p, 10, "slashing")
    assert p.hp == 1 and not p.defeated
    cb._apply_damage(st, p, 10, "slashing")
    assert p.defeated


def test_uncanny_dodge_halves_first_hit_each_round():
    p = player(hp=30, max_hp=30, halve_first_hit=True)
    st = EncounterState(location="t", combatants={"p1": p})
    cb._apply_damage(st, p, 10, "x")
    cb._apply_damage(st, p, 10, "x")
    assert p.hp == 30 - 5 - 10


def test_sneak_attack_with_hidden_advantage():
    rng = random.Random(11)
    rogue = player(attacks=[DAGGER], sneak_dice=2, abilities={"cunning_hide": None})
    target = monster(hp=500, max_hp=500, ac=1)
    st = encounter(rogue, target, rng=rng)
    st.combatants["p1"].statuses["hidden"] = 99
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), rng, ABILITIES)
    hit = next(e for e in logs if e.key in ("combat.hit", "combat.crit"))
    assert hit.params["sneak"] > 0
    assert "hidden" not in st.combatants["p1"].statuses


def test_flee_success_ends_encounter():
    rng = random.Random(0)
    st = encounter(player(skill_bonus={"athletics": 30}), monster(), rng=rng)
    cb.player_act(st, "p1", Action(kind="flee"), rng, ABILITIES)
    assert st.status == "fled"


def test_interact_scene_object_all_enemies():
    rng = random.Random(0)
    st = EncounterState(
        location="t",
        combatants={"p1": player(skill_bonus={"athletics": 30}), "m1": monster("m1", hp=50, max_hp=50),
                    "m2": monster("m2", hp=50, max_hp=50)},
        scene_objects={"nest": cb.SceneObjectState(key="nest", skill="athletics", tier="easy", damage="1d4",
                                                    targets="all_enemies", status={"status": "poisoned", "turns": 2})},
    )
    cb.start(st, rng)
    cb.player_act(st, "p1", Action(kind="interact", object="nest"), rng, ABILITIES)
    assert "nest" not in st.scene_objects
    assert all(st.combatants[m].hp < 50 for m in ("m1", "m2"))


def test_cowardly_enemy_flees_when_low():
    st = encounter(player(), monster("m1", cowardly=True), monster("m2"))
    me = st.combatants["m1"]
    me.hp = 2
    logs = cb._enemy_turn(st, me, random.Random(0))
    assert me.fled and logs[0].key == "combat.enemy_flees"


def test_actions_after_end_rejected():
    st = encounter(player(), monster())
    st.status = "victory"
    with pytest.raises(CombatError):
        cb.player_act(st, "p1", Action(kind="defend"), random.Random(0), ABILITIES)


def test_state_roundtrips_through_json():
    st = encounter(player(), monster())
    again = EncounterState.model_validate(st.model_dump(mode="json"))
    assert again == st
