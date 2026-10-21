"""The effective build and the hybrid level: XP proves experience, a milestone opens a border.

The rules themselves are in planning/roadmap_balance.md §4; the obligatory cases of §4.2 that need
the database (turning a mission in, paying once) belong to the services tests, not here.
"""

import pytest

from oathforge.content import get_content
from oathforge.content.schemas import Progression
from oathforge.engine import class_build as cb

ASH, STAG = "ash_collector", "iron_stag"


def prog() -> Progression:
    return get_content().progression


def test_the_table_covers_the_twenty_levels():
    p = prog()
    assert len(p.xp) == 20
    assert cb.level_for_xp(0, p) == 1 and cb.level_for_xp(p.xp[-1], p) == 20
    assert cb.level_for_xp(p.xp[-1] * 10, p) == 20  # no level 21 by hoarding XP
    assert cb.level_for_xp(p.xp[9] - 1, p) == 9 and cb.level_for_xp(p.xp[9], p) == 10


def test_xp_alone_never_opens_the_tenth_level():
    p, rich = prog(), prog().xp[9]
    assert cb.level_for_xp(rich, p) == 10
    assert cb.eligible_level(rich, [], p) == 9  # the Collector has not been turned in
    assert cb.blocked_by(rich, [], p) == ASH
    assert cb.eligible_level(rich, [ASH], p) == 10
    assert cb.blocked_by(rich, [ASH], p) is None


def test_the_milestone_alone_grants_nothing():
    p = prog()
    assert cb.eligible_level(0, [ASH, STAG], p) == 1  # no XP, no level, however many bosses fell
    assert cb.eligible_level(p.xp[4], [ASH], p) == 5


def test_xp_waiting_at_a_gate_is_kept_and_then_applied():
    """§4.2: earning the XP later takes the hero up without killing the Collector twice."""
    p, rich = prog(), prog().xp[11]
    assert cb.eligible_level(rich, [], p) == 9 and cb.eligible_level(rich, [ASH], p) == 10
    assert cb.eligible_level(rich, [ASH, STAG], p) == 12  # the Stag opens the rest of the road
    assert cb.xp_to_next(rich, p) == p.xp[12] - rich  # the XP never stopped counting


def test_unknown_milestones_and_the_top_of_the_table():
    p = prog()
    assert cb.cap_for(["made_up"], p) == p.base_cap
    assert cb.xp_to_next(p.xp[-1], p) is None
    assert cb.eligible_level(10 ** 9, [ASH, STAG], p) == len(p.xp)


def test_choices_queue_up_and_are_not_lost():
    p = prog()
    assert cb.pending_choices(4, {}, p) == ()
    assert [c.key for c in cb.pending_choices(13, {}, p)] == ["training:5", "training:12", "modifier:13"]
    # jumping from 4 to 13 in one go still owes the training of level 5
    assert [c.key for c in cb.pending_choices(13, {"modifier:13": "a"}, p)] == ["training:5", "training:12"]
    assert cb.pending_choices(20, {}, p, specialized=False) == \
        tuple(cb.Choice(cb.TRAINING, lvl) for lvl in p.training_levels)  # no branch, no modifiers


def test_a_resource_grows_with_the_level():
    p = prog()
    mana = p.resources["mana"]
    assert cb.resource_max(mana, 1) < cb.resource_max(mana, 10) < cb.resource_max(mana, 20)
    assert all(cb.resource_max(r, 1) > 0 for r in p.resources.values())  # nobody starts with an empty cap


def test_the_build_only_shows_what_the_level_reached():
    c, p = get_content(), prog()
    cls = c.classes["paladin"]
    low = cb.build_for("paladin", cls, 1, p)
    high = cb.build_for("paladin", cls, 5, p)
    assert set(low.abilities) < set(high.abilities)
    assert all(a.level <= 1 for a in low.abilities.values())
    assert "extra_attack" in high.passives() and "extra_attack" not in high.usable()


def test_a_branch_of_another_class_is_refused():
    c, p = get_content(), prog()
    with pytest.raises(ValueError):
        cb.build_for("paladin", c.classes["paladin"], 10, p,
                     specialization="pyromancer", branch=c.class_specializations["pyromancer"])


def test_a_branch_that_is_not_ready_or_comes_too_early_does_not_apply():
    c, p = get_content(), prog()
    avenger = c.class_specializations["avenger"]
    assert cb.build_for("paladin", c.classes["paladin"], 10, p,
                        specialization="avenger", branch=avenger).specialization is None  # not ready yet
    ready = avenger.model_copy(update={"ready": True})
    assert cb.build_for("paladin", c.classes["paladin"], 10, p,
                        specialization="avenger", branch=ready).specialization == "avenger"
    early = cb.build_for("paladin", c.classes["paladin"], p.specialization_level - 1, p,
                         specialization="avenger", branch=ready)
    assert early.specialization is None and not any(ch.kind == cb.MODIFIER for ch in early.pending)
