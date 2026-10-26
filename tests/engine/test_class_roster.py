"""The base classes of B06 (levels 1-9), all of them, whatever their number is today.

roadmap_balance §5.2, §11.2 and the B06 gate: every class has a useful basic attack and a distinctive
technique from level 1, its own bar, nothing that needs a branch, a trade or somebody else's help, and it
wins the introductory fights. These are floors, not balance claims: the figures are seeds (B12 measures them).
"""

import random

import pytest

from oathforge.content import get_content
from oathforge.engine import class_build
from oathforge.engine import combat as cb
from oathforge.engine.combat import AttackProfile, Combatant, EncounterState
from oathforge.tools import simulate as sim

CLASSES = sorted(get_content().classes)
BASE_MAX_LEVEL = 9  # the branch starts at 10 (class_specializations.yaml)


# ------------------------------------------------------------- what every class must have


@pytest.mark.parametrize("key", CLASSES)
def test_a_class_has_its_own_bar_and_a_featured_technique_from_level_one(key):
    c = get_content()
    cls = c.classes[key]
    assert cls.resource in c.progression.resources, f"{key} needs a bar"
    first = {k: a for k, a in cls.abilities.items() if a.level == 1}
    actives = {k: a for k, a in first.items() if a.kind != "passive"}
    assert actives, f"{key} has nothing to press at level 1"
    assert cls.signature and all(s in cls.abilities for s in cls.signature)
    bar_at_1 = class_build.resource_max(c.progression.resources[cls.resource], 1)
    assert any(a.cost <= bar_at_1 for a in actives.values()), f"{key} cannot pay for anything at level 1"


@pytest.mark.parametrize("key", CLASSES)
def test_a_class_never_needs_a_branch_a_trade_or_another_player(key):
    cls = get_content().classes[key]
    for akey, a in cls.abilities.items():
        assert a.level <= BASE_MAX_LEVEL, f"{key}.{akey}: levels 10-20 belong to the branch"
        assert a.entity is None, f"{key}.{akey}: helpers come with a branch (roadmap_balance §7)"
        assert a.kind not in ("summon", "command", "converge", "shift"), f"{key}.{akey}"


@pytest.mark.parametrize("key", CLASSES)
def test_the_calendar_of_powers_is_not_a_new_button_every_level(key):
    """§5.2: levels 6-9 give one or two improvements, not an obligatory ability each level."""
    cls = get_content().classes[key]
    by_level = {}
    for a in cls.abilities.values():
        by_level.setdefault(a.level, []).append(a)
    late = [a for lvl, group in by_level.items() if lvl >= 6 for a in group]
    assert 1 <= len(late) <= 4, f"{key} has {len(late)} abilities from level 6 on"
    assert all(len(group) <= 3 for group in by_level.values()), key  # nothing is dumped on a single level
    assert max(by_level) >= 6  # and it does keep growing past the training level


@pytest.mark.parametrize("key", CLASSES)
def test_starting_gear_equips_and_gives_a_free_attack(key):
    c = get_content()
    cls = c.classes[key]
    for item in cls.equip:
        assert item in cls.items, f"{key}: equips {item} without owning it"
    char = sim.sim_character(key, 1, "human", "soldier")
    gear = sim.sim_gear(char)
    from oathforge.services import characters

    attacks = characters.attack_profiles(char, gear)
    assert attacks and all(a.damage for a in attacks)  # never a class with nothing to hit with


@pytest.mark.parametrize("key", CLASSES)
def test_the_bar_of_a_class_that_builds_up_can_actually_be_built(key):
    """A class that starts at zero must be able to earn what its first technique costs."""
    c = get_content()
    cls = c.classes[key]
    res = c.progression.resources[cls.resource]
    if not res.starts_empty:
        return
    gains = res.per_turn + cls.resource_on_attack + max((a.generates for a in cls.abilities.values()), default=0)
    assert gains > 0, f"{key} starts empty and never earns anything"
    cheapest = min(a.cost for a in cls.abilities.values() if a.kind != "passive" and a.cost)
    assert cheapest <= class_build.resource_max(res, 2) and gains * 3 >= cheapest, key


# ----------------------------------------------------------------- the introductory fights


@pytest.mark.parametrize("level", [1, 3, 5, 9])
@pytest.mark.parametrize("key", CLASSES)
def test_every_class_beats_a_bandit(key, level):
    rows = sim.simulate([key], ["bandit"], [level], n=40, seed=11, lineage="human", background="soldier")
    assert rows[0]["win_pct"] >= 90, f"{key} L{level}: {rows[0]['win_pct']}% against a bandit"
    assert rows[0]["timeout_pct"] == 0


@pytest.mark.parametrize("level", [5, 9])
@pytest.mark.parametrize("key", CLASSES)
def test_every_class_handles_a_pair_from_level_five(key, level):
    rows = sim.simulate(
        [key], ["goblin_scout+goblin_scout"], [level], n=40, seed=11, lineage="human", background="soldier"
    )
    assert rows[0]["win_pct"] >= 85, f"{key} L{level}: {rows[0]['win_pct']}% against a pair of goblins"


@pytest.mark.parametrize("level", [3, 5, 9])
@pytest.mark.parametrize("key", CLASSES)
def test_several_fights_in_a_row_without_a_full_rest(key, level):
    """The bar runs down and comes back by its rules; it never leaves its range; a free attack is always there."""
    c = get_content()
    me, defs = sim.hero(key, level, "human", "soldier")
    starts_empty = c.progression.resources[c.classes[key].resource].starts_empty
    rng = random.Random(21)
    for n in range(3):
        foe = Combatant(
            id="m1",
            side="enemy",
            ref="x",
            name={"es": "x", "en": "x"},
            hp=20,
            max_hp=20,
            ac=11,
            dex_mod=0,
            xp=1,
            attacks=[
                AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=4, damage="1d6+1", damage_type="slashing")
            ],
        )
        state = EncounterState(location="simulation", combatants={"p1": me, "m1": foe})
        me.defeated = me.fled = False
        me.resource = 0 if starts_empty else me.resource  # a new fight: that kind of bar starts empty
        cb.start(state, rng)
        for _ in range(40):
            if state.status != "active":
                break
            sim.play_turn(state, rng, defs)
            assert 0 <= me.resource <= me.resource_max
            assert me.attacks and all(a.damage for a in me.attacks)
        if state.status != "victory":
            break  # the hero ran out of life: the bar was never the reason, which is all this checks
        me.hp = max(1, me.hp)  # no full rest in between: whatever was left stays
    assert 0 <= me.resource <= me.resource_max


# -------------------------------------------------------------------- engine pieces of B06


def dummy(**kw) -> Combatant:
    base = dict(
        id="m1",
        side="enemy",
        ref="x",
        name={"es": "x", "en": "x"},
        hp=400,
        max_hp=400,
        ac=1,
        dex_mod=-10,
        xp=1,
        attacks=[AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=-99, damage="1d1", damage_type="slashing")],
    )
    base.update(kw)
    return Combatant(**base)


def test_a_ranged_strike_uses_the_bow_and_a_melee_one_the_blade():
    from oathforge.content.schemas import ClassAbility, Text

    t = Text(es="x", en="x")

    def ab(**kw):
        return ClassAbility(
            name=t, description=t, level=1, kind="strike", extra_damage="1d4", damage_type="piercing", **kw
        )

    sword = AttackProfile(
        key="main", name={"es": "Espada", "en": "Sword"}, to_hit=99, damage="1d1", damage_type="slashing"
    )
    bow = AttackProfile(
        key="ranged", name={"es": "Arco", "en": "Bow"}, to_hit=99, damage="1d1", damage_type="piercing", ranged=True
    )
    defs = {"shot": ab(ranged=True), "cut": ab()}
    me = Combatant(
        id="p1",
        side="player",
        ref="1",
        name={"es": "H", "en": "H"},
        hp=20,
        max_hp=20,
        ac=12,
        attacks=[sword, bow],
        abilities={"shot": None, "cut": None},
        row="back",
    )
    state = EncounterState(location="t", combatants={"p1": me, "m1": dummy()})
    state.order, state.turn_index = ["p1", "m1"], 0
    used = []
    for key in ("shot", "cut"):
        me.action_used = False
        logs = cb.player_act(state, "p1", cb.Action(kind="ability", ability=key, target="m1"), random.Random(2), defs)
        used.append(next(e.params["weapon"] for e in logs if e.key in ("combat.hit", "combat.crit"))["en"])
    assert used == ["Bow", "Sword"]


def test_a_marked_quarry_takes_an_extra_die_from_every_hit_of_its_hunter():
    me = Combatant(
        id="p1",
        side="player",
        ref="1",
        name={"es": "H", "en": "H"},
        hp=20,
        max_hp=20,
        ac=12,
        attacks=[
            AttackProfile(key="main", name={"es": "E", "en": "S"}, to_hit=99, damage="1d1", damage_type="slashing")
        ],
    )
    foe = dummy()
    state = EncounterState(location="t", combatants={"p1": me, "m1": foe})
    state.order, state.turn_index = ["p1", "m1"], 0
    cb._apply_status(foe, "marked", 3)
    seen = 0
    for seed in range(20):
        before = foe.hp
        logs = cb._attack(state, me, foe, me.attacks[0], random.Random(seed), None)
        if any(e.key in ("combat.hit", "combat.crit") for e in logs):
            seen += 1
            assert any(e.key == "combat.damage" and e.params["type"] == "piercing" for e in logs)  # the die
            assert before - foe.hp >= 2  # the 1 from the weapon plus at least 1 from the mark
    assert seen > 10


def test_the_monk_hits_with_dexterity_and_dresses_in_discipline():
    from oathforge.services import characters

    char = sim.sim_character("monk", 1, "human", "soldier")
    gear = sim.sim_gear(char)
    main = next(a for a in characters.attack_profiles(char, gear) if a.key == "main")
    assert main.finesse and main.to_hit == characters.mods(char)["dex"] + 2  # DEX, since the wraps are light
    assert "body" not in gear
    assert characters.armor_class(char, gear) == 10 + characters.mods(char)["dex"] + 3  # unarmored defense
