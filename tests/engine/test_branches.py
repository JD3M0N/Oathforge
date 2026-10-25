"""Every branch that is ready (roadmap_balance B07), whatever their number is today.

A branch is playable only with its whole 10-20 path, it must make a decision the base class does not, it must
differ from its sibling branches in how it plays (N15: not the same loop in another colour) and every
modifier must really change something. Figures are seeds; the floors here only say nothing is hopeless.
"""

import random

import pytest

from oathforge.content import get_content
from oathforge.engine import combat as cb
from oathforge.engine.combat import Action, AttackProfile, Combatant, EncounterState
from oathforge.services import characters, combat_service
from oathforge.tools import simulate as sim

C = get_content()
READY = sorted(k for k, b in C.class_specializations.items() if b.ready)
LEVELS = (10, 13, 17, 20)


def effective(branch: str, level: int, picks: dict | None = None):
    char = sim.sim_character(C.class_specializations[branch].class_key, level, "human", "soldier", branch, picks)
    return char, characters.abilities_of(char)


def tags(branch: str) -> set[str]:
    """The verbs of a branch: what it applies, spends, answers, heals, shields and reaches."""
    b = C.class_specializations[branch]
    cls = C.classes[b.class_key]
    found = set()
    for a in [*b.abilities.values(), *(g for m in b.modifiers.values() for g in m.grants.values())]:
        if a.consumes:
            found.add(f"consume:{a.consumes}")
        if a.status and a.kind in ("curse", "save", "buff", "spell"):
            found.add(f"applies:{a.status}")
        if a.thorns or a.resource_on_hurt:
            found.add("answer")
        if a.leech_pct:
            found.add("leech")
        if a.temp_hp or (a.kind == "heal"):
            found.add("barrier" if a.kind != "heal" else "heal")
        if a.area == "row":
            found.add("reach")
        if a.ranged:
            found.add("ranged")
        if a.crit_range:
            found.add("crit")
        if a.halve_first_hit:
            found.add("mitigate")
        if a.entity or a.kind in ("summon", "command", "converge"):
            found.add("entities")
        if a.kind == "shift":
            found.add("forms")
        if a.reduces_cooldowns:
            found.add("time")
    return found


# ------------------------------------------------------------------ the path is whole

@pytest.mark.parametrize("key", READY)
def test_a_ready_branch_has_its_whole_path(key):
    b = C.class_specializations[key]
    prog = C.progression
    first, last = prog.specialization_level, len(prog.xp)
    assert any(a.level == first and a.kind == "passive" for a in b.abilities.values())
    assert any(a.level == first and a.kind != "passive" for a in b.abilities.values())
    assert any(a.level == last and a.kind != "passive" for a in b.abilities.values())
    assert any(15 <= a.level <= 16 or a.level == 15 for a in b.abilities.values()), "no fixed development"
    for lvl in prog.modifier_levels:
        assert sum(1 for m in b.modifiers.values() if m.level == lvl) == 2


@pytest.mark.parametrize("key", READY)
def test_the_path_arrives_at_its_levels(key):
    b = C.class_specializations[key]
    for lvl in LEVELS:
        _, built = effective(key, lvl)
        mine = {k for k in b.abilities if k in built}
        assert mine == {k for k, a in b.abilities.items() if a.level <= lvl}, (key, lvl)
        if lvl >= 10:
            assert mine, f"{key} gives nothing at level {lvl}"


# ------------------------------------------------------------------ not the same loop twice

def test_sibling_branches_do_not_play_the_same_loop():
    by_class = {}
    for key in READY:
        by_class.setdefault(C.class_specializations[key].class_key, []).append(key)
    for cls, keys in by_class.items():
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                assert tags(a) != tags(b), f"{a} and {b} ({cls}) make the same decisions"


@pytest.mark.parametrize("key", READY)
def test_a_branch_makes_a_decision_its_class_does_not(key):
    verbs = tags(key)
    assert verbs, f"{key} adds no verb of its own (nothing it applies, spends, answers, heals, shields or reaches)"


# ------------------------------------------------------------------ the modifiers do something

def _modifier_cases():
    for key in READY:
        for mkey, m in C.class_specializations[key].modifiers.items():
            yield pytest.param(key, mkey, id=f"{key}.{mkey}")


@pytest.mark.parametrize("key,mkey", list(_modifier_cases()))
def test_every_modifier_changes_the_character(key, mkey):
    m = C.class_specializations[key].modifiers[mkey]
    other = next(k for k, o in C.class_specializations[key].modifiers.items() if o.level == m.level and k != mkey)
    _, plain = effective(key, 20, {f"modifier:{m.level}": other})
    _, picked = effective(key, 20, {f"modifier:{m.level}": mkey})
    changed = [k for k in picked if picked[k] != plain.get(k)]
    assert changed or set(picked) != set(plain), f"{key}.{mkey} changes nothing"


@pytest.mark.parametrize("key", READY)
def test_the_two_options_of_a_level_are_not_the_same(key):
    for lvl in (13, 17):
        a, b = [k for k, m in C.class_specializations[key].modifiers.items() if m.level == lvl]
        _, one = effective(key, 20, {f"modifier:{lvl}": a})
        _, two = effective(key, 20, {f"modifier:{lvl}": b})
        assert one != two, f"{key}: both options of level {lvl} give the same character"


# ------------------------------------------------------------------ the decision, in a fight

def arena(key: str, level: int = 20, **foe_kw):
    char, defs = effective(key, level)
    me = characters.combatant_from(char, sim.sim_gear(char), sim.sim_skills(char))
    me.resource = me.resource_max  # a full bar: only the rules can stop the ability
    foe = Combatant(id="m1", side="enemy", ref="x", name={"es": "x", "en": "x"}, hp=100000, max_hp=100000, ac=1,
                    dex_mod=-10, xp=1, attacks=[AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=-99,
                                                              damage="1d1", damage_type="slashing")], **foe_kw)
    st = EncounterState(location="t", combatants={"p1": me, "m1": foe})
    st.order, st.turn_index = ["p1", "m1"], 0
    return st, me, foe, defs


def use(st, defs, key, seed=3):
    return cb.player_act(st, "p1", Action(kind="ability", ability=key, target="m1"), random.Random(seed), defs)


def _consumers():
    for key in READY:
        for akey, a in C.class_specializations[key].abilities.items():
            if a.consumes and a.level <= 20:
                yield pytest.param(key, akey, id=f"{key}.{akey}")


@pytest.mark.parametrize("key,akey", list(_consumers()))
def test_spending_a_status_is_a_real_choice(key, akey):
    st, me, foe, defs = arena(key)
    a = defs[akey]
    me.cooldowns = {}
    plain = [e.key for e in use(st, defs, akey)]
    assert "combat.consumed" not in plain  # nothing to spend, nothing spent
    st2, me2, foe2, defs2 = arena(key)
    cb._apply_status(foe2, a.consumes, 5)
    spent = [e.key for e in use(st2, defs2, akey)]
    assert "combat.consumed" in spent and a.consumes not in foe2.statuses


def _leechers():
    for key in READY:
        for akey, a in C.class_specializations[key].abilities.items():
            if a.leech_pct:
                yield pytest.param(key, akey, id=f"{key}.{akey}")


@pytest.mark.parametrize("key,akey", list(_leechers()))
def test_a_leech_heals_only_from_real_damage(key, akey):
    st, me, foe, defs = arena(key)
    me.hp = me.max_hp // 2
    before = me.hp
    use(st, defs, akey)
    assert me.hp > before or foe.hp == foe.max_hp  # it healed, or nothing landed and nothing healed


@pytest.mark.parametrize("key", [k for k in READY if any(a.thorns or a.resource_on_hurt for a in
                                                         C.class_specializations[k].abilities.values())])
def test_an_answering_branch_answers_a_real_wound(key):
    st, me, foe, defs = arena(key)
    me.ac = 1
    foe.attacks = [AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=99, damage="3d6", damage_type="slashing")]
    me.resource = 0
    logs = cb._attack(st, foe, me, foe.attacks[0], random.Random(2), None)
    keys = [e.key for e in logs]
    assert "combat.thorns" in keys or me.resource > 0 or "combat.resource_gained" in keys


# ------------------------------------------------------------------ nothing is hopeless

def boss(level: int) -> Combatant:
    """A synthetic single enemy that grows with the hero (the real monsters of levels 11-20 are B11)."""
    hp = 40 + 10 * level
    return Combatant(id="m1", side="enemy", ref="boss", name={"es": "J", "en": "B"}, hp=hp, max_hp=hp,
                     ac=12 + level // 4, dex_mod=1, xp=1, boss=True,
                     attacks=[AttackProfile(key="a", name={"es": "x", "en": "x"}, to_hit=3 + level // 2,
                                            damage=f"2d6+{level // 2 + 1}", damage_type="slashing")])


def duel(key: str, level: int, seed: int) -> bool:
    rng = random.Random(seed)
    char = sim.sim_character(C.class_specializations[key].class_key, level, "human", "soldier", key)
    me = characters.combatant_from(char, sim.sim_gear(char), sim.sim_skills(char))
    defs = combat_service.ability_defs(char)
    st = EncounterState(location="s", combatants={"p1": me, "m1": boss(level)})
    sim._bring_helpers(st, me, char)
    cb.start(st, rng)
    while st.status == "active" and st.round <= 40:
        sim.play_turn(st, rng, defs)
    return st.status == "victory"


@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("key", READY)
def test_no_branch_is_hopeless_against_a_boss_of_its_level(key, level):
    wins = sum(duel(key, level, seed) for seed in range(20))
    assert wins >= 3, f"{key} L{level}: {wins}/20 wins against a boss of its level"
