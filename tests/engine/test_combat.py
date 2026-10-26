import random

import pytest

from oathforge.content import get_content
from oathforge.engine import combat as cb
from oathforge.engine.combat import Action, AttackProfile, Combatant, CombatError, EncounterState

_CLASSES = get_content().classes
ABILITIES = {k: a for cls in _CLASSES.values() for k, a in cls.abilities.items()}
SWORD = AttackProfile(
    key="main", name={"es": "Espada", "en": "Sword"}, to_hit=5, damage="1d8+3", damage_type="slashing"
)
BOW = AttackProfile(
    key="ranged", name={"es": "Arco", "en": "Bow"}, to_hit=5, damage="1d6+3", damage_type="piercing", ranged=True
)
DAGGER = AttackProfile(
    key="main", name={"es": "Daga", "en": "Dagger"}, to_hit=5, damage="1d4+3", damage_type="piercing", finesse=True
)


def player(**kw) -> Combatant:
    base = dict(
        id="p1",
        side="player",
        ref="1",
        name={"es": "Aldric", "en": "Aldric"},
        hp=20,
        max_hp=20,
        ac=16,
        dex_mod=0,
        attacks=[SWORD],
        skill_bonus={"athletics": 5, "stealth": 5},
    )
    base.update(kw)
    return Combatant(**base)


def monster(cid="m1", **kw) -> Combatant:
    base = dict(
        id=cid,
        side="enemy",
        ref="bandit",
        name={"es": "Bandido", "en": "Bandit"},
        hp=11,
        max_hp=11,
        ac=12,
        dex_mod=1,
        attacks=[AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=3, damage="1d6+1", damage_type="slashing")],
        xp=25,
    )
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
        combatants={
            "p1": player(skill_bonus={"athletics": 30}),
            "m1": monster("m1", hp=50, max_hp=50),
            "m2": monster("m2", hp=50, max_hp=50),
        },
        scene_objects={
            "nest": cb.SceneObjectState(
                key="nest",
                skill="athletics",
                tier="easy",
                damage="1d4",
                targets="all_enemies",
                status={"status": "poisoned", "turns": 2},
            )
        },
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


# ---------------------------------------------------------------- v0.2.0: damage types, warrior, cleric


class FixedRng(random.Random):
    """Every die shows ``value`` (capped at the die size)."""

    def __init__(self, value: int):
        super().__init__(0)
        self.value = value

    def randint(self, a, b):
        return min(b, max(a, self.value))


def started(*cs) -> EncounterState:
    """Encounter where the player acts first, without rolling initiative."""
    st = EncounterState(location="t", combatants={c.id: c for c in cs}, order=[c.id for c in cs])
    return st


def test_damage_types_weak_resist_immune():
    m = monster(hp=100, max_hp=100, weak_to=["radiant"], resist=["slashing"], immune_damage=["poison"])
    st = EncounterState(location="t", combatants={"m1": m})
    weak = cb._apply_damage(st, m, 10, "radiant")[0]
    resist = cb._apply_damage(st, m, 10, "slashing")[0]
    immune = cb._apply_damage(st, m, 10, "poison")[0]
    plain = cb._apply_damage(st, m, 10, "piercing")[0]
    assert [e.params["amount"] for e in (weak, resist, immune, plain)] == [20, 5, 0, 10]
    assert [e.params["effect"] for e in (weak, resist, immune, plain)] == ["weak", "resist", "immune", ""]
    assert m.hp == 100 - 35


def test_extra_radiant_damage_is_applied_separately():
    st = started(player(abilities={"consecrated_strike": 1}), monster(hp=100, max_hp=100, ac=1, weak_to=["radiant"]))
    logs = cb.player_act(
        st, "p1", Action(kind="ability", ability="consecrated_strike", target="m1"), FixedRng(4), ABILITIES
    )
    dmg = [e.params for e in logs if e.key == "combat.damage" and e.params["target"] == "m1"]
    assert [(d["type"], d["amount"], d["effect"]) for d in dmg] == [("slashing", 4 + 3, ""), ("radiant", 8, "weak")]


def test_improved_critical_on_19():
    st = started(player(crit_range=19), monster(hp=100, max_hp=100, ac=30))
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(19), ABILITIES)
    assert any(e.key == "combat.crit" for e in logs)
    st = started(player(), monster(hp=100, max_hp=100, ac=10))
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(19), ABILITIES)
    assert not any(e.key == "combat.crit" for e in logs) and any(e.key == "combat.hit" for e in logs)


def test_action_surge_gives_the_action_back():
    st = started(player(abilities={"action_surge": 1, "second_wind": 1}), monster(hp=100, max_hp=100))
    with pytest.raises(CombatError) as e:
        cb.player_act(st, "p1", Action(kind="ability", ability="action_surge"), FixedRng(10), ABILITIES)
    assert e.value.key == "combat.err.surge_unused"
    cb.player_act(st, "p1", Action(kind="defend"), FixedRng(10), ABILITIES)
    assert st.current.id == "p1" and "action_surge" in cb.available_bonus_actions(st, st.current, ABILITIES)
    cb.player_act(st, "p1", Action(kind="ability", ability="action_surge"), FixedRng(10), ABILITIES)
    p = st.combatants["p1"]
    assert not p.action_used and p.bonus_used and p.abilities["action_surge"] == 0
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(10), ABILITIES)
    assert any(e.key == "combat.hit" for e in logs) and st.round == 2  # second action, then the turn ends


def test_second_wind_heals_dice_plus_level():
    st = started(player(hp=1, level=3, abilities={"second_wind": 1}), monster())
    cb.player_act(st, "p1", Action(kind="ability", ability="second_wind"), FixedRng(6), ABILITIES)
    assert st.combatants["p1"].hp == 1 + 6 + 3


def test_sacred_flame_uses_spell_bonus_and_reaches_back_row():
    cleric = player(row="back", attacks=[], spell_to_hit=4, abilities={"sacred_flame": None})
    archer = monster(row="back", hp=100, max_hp=100, ac=14)
    st = started(cleric, monster("m2"), archer)
    logs = cb.player_act(st, "p1", Action(kind="ability", ability="sacred_flame", target="m1"), FixedRng(10), ABILITIES)
    hit = next(e for e in logs if e.key == "combat.hit")
    assert hit.params["total"] == 14 and hit.params["target"] == "m1"
    dmg = next(e for e in logs if e.key == "combat.damage" and e.params["target"] == "m1")
    assert dmg.params["type"] == "radiant"
    assert st.combatants["p1"].abilities["sacred_flame"] is None  # unlimited


def test_turn_undead_only_hits_undead():
    st = started(
        player(abilities={"turn_undead": 1}),
        monster("m1", hp=50, max_hp=50, creature_type="undead", weak_to=["radiant"]),
        monster("m2", hp=50, max_hp=50),
    )
    logs = cb.player_act(st, "p1", Action(kind="ability", ability="turn_undead"), FixedRng(3), ABILITIES)
    assert st.combatants["m1"].hp == 50 - 12 and st.combatants["m2"].hp == 50
    assert any(e.key == "combat.status" and e.params["status"] == "stunned" for e in logs)
    st = started(player(abilities={"turn_undead": 1}), monster())
    with pytest.raises(CombatError) as e:
        cb.player_act(st, "p1", Action(kind="ability", ability="turn_undead"), FixedRng(3), ABILITIES)
    assert e.value.key == "combat.err.no_type_targets"


def test_bless_adds_to_attack_rolls_for_three_turns():
    st = started(player(abilities={"bless": 1}), monster(hp=500, max_hp=500, ac=30))
    cb.player_act(st, "p1", Action(kind="ability", ability="bless"), FixedRng(10), ABILITIES)
    totals = []
    for _ in range(4):
        cb.player_act(st, "p1", Action(kind="end_turn"), FixedRng(10), ABILITIES) if st.current.action_used else None
        logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(10), ABILITIES)
        totals.append(next(e for e in logs if e.key == "combat.miss").params["total"])
    assert totals == [17, 17, 17, 15]


def test_divine_strike_once_per_turn():
    st = started(player(bonus_damage="1d8", extra_attack=True), monster(hp=500, max_hp=500, ac=1))
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(5), ABILITIES)
    radiant = [e for e in logs if e.key == "combat.damage" and e.params["type"] == "radiant"]
    assert len(radiant) == 1


# ---------------------------------------------------------------- v0.4.0: sorcerer, druid, bard


def test_save_fails_below_dc_and_succeeds_at_dc():
    for value, slept in ((12, True), (13, False)):
        st = started(player(spell_dc=13, abilities={"sleep": 2}), monster(hp=100, max_hp=100))
        logs = cb.player_act(st, "p1", Action(kind="ability", ability="sleep", target="m1"), FixedRng(value), ABILITIES)
        save = next(e for e in logs if e.key == "combat.save")
        assert save.params["save"] == "wis" and save.params["dc"] == 13 and save.params["success"] is not slept
        assert any(e.key == "combat.status" and e.params["status"] == "asleep" for e in logs) is slept


def test_fireball_hits_the_targets_row_and_halves_on_save():
    def cast(value):
        st = started(
            player(spell_dc=13, abilities={"fireball": 1}),
            monster("m1", hp=50, max_hp=50),
            monster("m2", hp=50, max_hp=50),
            monster("m3", hp=50, max_hp=50, row="back"),
        )
        cb.player_act(st, "p1", Action(kind="ability", ability="fireball", target="m2"), FixedRng(value), ABILITIES)
        return [st.combatants[m].hp for m in ("m1", "m2", "m3")]

    assert cast(5) == [50 - 15, 50 - 15, 50]  # failed save: 3d6 = 15
    assert cast(15) == [50 - 9, 50 - 9, 50]  # saved (15 + 1 >= 13): half of 18


def test_sleep_skips_turns_and_damage_wakes():
    st = started(player(spell_dc=13, abilities={"sleep": 2}), monster(hp=100, max_hp=100, ac=10))
    logs = cb.player_act(st, "p1", Action(kind="ability", ability="sleep", target="m1"), FixedRng(1), ABILITIES)
    assert any(e.key == "combat.asleep" for e in logs) and st.current.id == "p1"
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(10), ABILITIES)
    hit = next(e for e in logs if e.key == "combat.hit")
    assert hit.params["adv"] and any(e.key == "combat.wake" for e in logs)
    assert "asleep" not in st.combatants["m1"].statuses


def test_restrained_gives_advantage_against_and_disadvantage_on_attacks():
    st = started(player(), monster(hp=100, max_hp=100, ac=1, statuses={"restrained": 2}))
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(10), ABILITIES)
    assert next(e for e in logs if e.key == "combat.hit").params["adv"]
    st = started(player(statuses={"restrained": 2}), monster(hp=100, max_hp=100, ac=1))
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(10), ABILITIES)
    assert next(e for e in logs if e.key == "combat.hit").params["dis"]


def test_inspiration_adds_a_d6_once():
    st = started(player(abilities={"bardic_inspiration": 2}), monster(hp=500, max_hp=500, ac=30))
    cb.player_act(st, "p1", Action(kind="ability", ability="bardic_inspiration"), FixedRng(10), ABILITIES)
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(10), ABILITIES)
    assert next(e for e in logs if e.key == "combat.miss").params["total"] == 10 + 5 + 6
    assert "inspired" not in st.combatants["p1"].statuses


def test_wild_shape_temp_hp_absorbs_damage_first():
    st = started(player(level=3, abilities={"wild_shape": 1}), monster())
    cb.player_act(st, "p1", Action(kind="ability", ability="wild_shape"), FixedRng(4), ABILITIES)
    p = st.combatants["p1"]
    assert p.temp_hp == 8 + 3 and "wild_shape" in p.statuses
    logs = cb._apply_damage(st, p, 14, "slashing")
    assert p.temp_hp == 0 and p.hp == 20 - 3
    assert any(e.key == "combat.absorbed" and e.params["amount"] == 11 for e in logs)


def test_magic_missile_never_misses_and_spell_damage_bonus():
    st = started(player(abilities={"magic_missile": 2}), monster(hp=100, max_hp=100, ac=99))
    logs = cb.player_act(st, "p1", Action(kind="ability", ability="magic_missile", target="m1"), FixedRng(1), ABILITIES)
    assert not any(e.key == "combat.miss" and e.params["actor"] == "p1" for e in logs)
    assert st.combatants["m1"].hp == 100 - 6
    st = started(
        player(spell_to_hit=5, spell_damage_bonus=3, abilities={"thorn_whip": None}), monster(hp=100, max_hp=100, ac=1)
    )
    cb.player_act(st, "p1", Action(kind="ability", ability="thorn_whip", target="m1"), FixedRng(2), ABILITIES)
    assert st.combatants["m1"].hp == 100 - (2 + 3)


def test_vicious_mockery_frightens_but_undead_are_immune():
    st = started(
        player(spell_dc=13, abilities={"vicious_mockery": None}), monster(hp=100, max_hp=100, immune=["frightened"])
    )
    logs = cb.player_act(
        st, "p1", Action(kind="ability", ability="vicious_mockery", target="m1"), FixedRng(2), ABILITIES
    )
    assert st.combatants["m1"].hp == 100 - 2 and any(e.key == "combat.immune" for e in logs)


# ---------------------------------------------------------------- v0.4.4: warlock


def test_hex_curses_without_save_and_uses_the_bonus_action():
    st = started(player(abilities={"hex": 2}), monster(hp=100, max_hp=100))
    logs = cb.player_act(st, "p1", Action(kind="ability", ability="hex", target="m1"), FixedRng(1), ABILITIES)
    assert not any(e.key == "combat.save" for e in logs)
    assert st.combatants["m1"].statuses["hexed"] == 3
    p = st.combatants["p1"]
    assert p.abilities["hex"] == 1 and p.bonus_used and not p.action_used


def test_hits_on_a_hexed_target_add_necrotic_damage():
    st = started(player(), monster(hp=100, max_hp=100, ac=1, statuses={"hexed": 3}))
    logs = cb.player_act(st, "p1", Action(kind="attack", weapon="main", target="m1"), FixedRng(2), ABILITIES)
    assert any(e.key == "combat.damage" and e.params["type"] == "necrotic" and e.params["amount"] == 2 for e in logs)
    assert st.combatants["m1"].hp == 100 - (2 + 3) - 2
    st = started(
        player(spell_to_hit=5, abilities={"eldritch_blast": None}),
        monster(hp=100, max_hp=100, ac=1, statuses={"hexed": 3}),
    )
    cb.player_act(st, "p1", Action(kind="ability", ability="eldritch_blast", target="m1"), FixedRng(2), ABILITIES)
    assert st.combatants["m1"].hp == 100 - 2 - 2


def test_hex_respects_immunity():
    st = started(player(abilities={"hex": 2}), monster(hp=100, max_hp=100, immune=["hexed"]))
    logs = cb.player_act(st, "p1", Action(kind="ability", ability="hex", target="m1"), FixedRng(1), ABILITIES)
    assert any(e.key == "combat.immune" for e in logs) and "hexed" not in st.combatants["m1"].statuses


ITEMS = {f"item:{k}": i.combat for k, i in get_content().items.items() if i.combat is not None}
NAMES = {k: i.name.model_dump() for k, i in get_content().items.items()}


def use(st, key, target=None, rng=None):
    action = Action(kind="item", ability=key, target=target, item_name=NAMES[key])
    return cb.player_act(st, "p1", action, rng or random.Random(1), {**ABILITIES, **ITEMS})


def test_combat_items_are_spent_once_and_need_stock():
    st = encounter(player(consumables={"scroll_firebolt": 1}), monster(hp=50, max_hp=50))
    use(st, "scroll_firebolt")
    assert st.combatants["p1"].consumables["scroll_firebolt"] == 0
    st.combatants["p1"].action_used = False
    with pytest.raises(CombatError):
        use(st, "scroll_firebolt")


def test_smoke_bomb_escapes_without_a_roll():
    st = encounter(player(consumables={"smoke_bomb": 1}), monster(), monster("m2"))
    logs = use(st, "smoke_bomb")
    assert st.status == "fled" and any(e.key == "combat.escaped" for e in logs)


def test_fire_bomb_burns_the_row_on_a_failed_save():
    st = encounter(
        player(consumables={"fire_bomb": 1}),
        monster(hp=99, max_hp=99, dex_mod=-10),
        monster("m2", hp=99, max_hp=99, dex_mod=-10),
    )
    use(st, "fire_bomb", target="m1")
    for m in ("m1", "m2"):
        assert st.combatants[m].hp < 99


def test_cure_scroll_heals_any_class():
    st = encounter(player(hp=5, consumables={"scroll_cure": 1}), monster())
    use(st, "scroll_cure")
    assert st.combatants["p1"].hp > 5 or st.status != "active"
