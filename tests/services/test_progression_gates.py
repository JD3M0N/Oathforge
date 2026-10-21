"""The hybrid level and handing missions in: the obligatory cases of roadmap_balance §4.2.

XP proves experience and a milestone opens a narrative border, and both are needed. Nothing is paid
until the mission reaches the one who gave it, and it is paid exactly once.
"""

import random

import pytest
from sqlalchemy import select

from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.services import characters, quests
from oathforge.services.events import Outcome

pytestmark = pytest.mark.usefixtures("database")

ASH, STAG = "ash_collector", "iron_stag"
TUSK = "old_tusk"  # the only mission handed in today; the campaign of B09 works the same way


def xp_for(level: int) -> int:
    return get_content().progression.xp[level - 1]


async def new_character(tg_id=1) -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, tg_id, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        return char.id


async def get_char(s, char_id) -> Character:
    return await s.scalar(select(Character).where(Character.id == char_id).with_for_update())


# ------------------------------------------------------- the hybrid level

async def test_all_the_xp_in_the_world_does_not_open_the_tenth_level():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        characters.grant_xp(char, xp_for(12), Outcome())
        assert char.level == 9  # the Collector was never handed in
        assert char.xp == xp_for(12)  # and the XP is kept, every point of it
        assert characters.level_gate(char) == ASH


async def test_the_milestone_opens_the_level_the_xp_already_paid_for():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = Outcome()
        characters.grant_xp(char, xp_for(10), out)
        assert char.level == 9
        assert characters.grant_milestone(char, ASH, out)
        assert char.level == 10 and characters.level_gate(char) is None
        assert [e.key for e in out.events if e.key == "progress.milestone"]


async def test_a_milestone_on_its_own_grants_nothing():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert characters.grant_milestone(char, ASH, Outcome())
        assert char.level == 1  # no XP, no level, however many bosses fell
        characters.grant_xp(char, xp_for(10), Outcome())
        assert char.level == 10  # and now, without killing anything twice


async def test_a_milestone_is_granted_once_and_an_unknown_one_never():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert characters.grant_milestone(char, ASH, Outcome())
        assert not characters.grant_milestone(char, ASH, Outcome())
        assert not characters.grant_milestone(char, "made_up", Outcome())
        assert characters.milestones_of(char) == [ASH]


async def test_the_second_gate_holds_the_hero_at_ten():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        characters.grant_xp(char, xp_for(14), Outcome())
        characters.grant_milestone(char, ASH, Outcome())
        assert char.level == 10 and characters.level_gate(char) == STAG  # the Stag is still owed
        characters.grant_milestone(char, STAG, Outcome())
        assert char.level == 14


async def test_the_gate_survives_a_reload():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        characters.grant_xp(char, xp_for(11), Outcome())
        characters.grant_milestone(char, ASH, Outcome())
    async with session_scope() as s:  # a fresh transaction sees the same thing
        char = await get_char(s, cid)
        assert char.level == 10 and characters.milestones_of(char) == [ASH]
        assert characters.eligible_level(char) == 10 and characters.level_gate(char) == STAG


# ------------------------------------------------------ handing a mission in

async def ready_tusk(s, char, rng) -> None:
    """Take the character to the point where Old Tusk is down and Bram is owed the news."""
    await quests.ensure_progress(s, char)
    prog = (await quests.progress(s, char))[TUSK]
    prog.stage, prog.state = "active", "active"
    await quests.on_defeat(s, char, TUSK, rng)


async def test_beating_the_boss_pays_nothing_until_the_giver_hears_it():
    cid = await new_character()
    rng = random.Random(1)
    async with session_scope() as s:
        char = await get_char(s, cid)
        gold, xp = char.gold, char.xp
        await ready_tusk(s, char, rng)
        assert (await quests.progress(s, char))[TUSK].state == "ready"
        assert (char.gold, char.xp) == (gold, xp)
        char.location = "broken_crown_tavern"
        assert [k for k, _ in await quests.ready_to_turn_in(s, char, ["bram"])] == [TUSK]
        assert await quests.ready_to_turn_in(s, char, ["vale"]) == []  # not his mission
        out = await quests.turn_in(s, char, TUSK, ["bram"], rng)
        assert out.ok and (char.gold, char.xp) == (gold + 80, xp + 300)
        assert (await quests.progress(s, char))[TUSK].state == "completed"


async def test_the_giver_has_to_be_there():
    cid = await new_character()
    rng = random.Random(2)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await ready_tusk(s, char, rng)
        gold = char.gold
        out = await quests.turn_in(s, char, TUSK, ["vale"], rng)
        assert not out.ok and out.error == "quest.err.giver_away" and char.gold == gold


async def test_handing_it_in_twice_pays_once():
    cid = await new_character()
    rng = random.Random(3)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await ready_tusk(s, char, rng)
        char.location = "broken_crown_tavern"
        gold, xp = char.gold, char.xp
        assert (await quests.turn_in(s, char, TUSK, ["bram"], rng)).ok
        for _ in range(3):  # a double tap, or an old menu still on screen
            again = await quests.turn_in(s, char, TUSK, ["bram"], rng)
            assert not again.ok and again.error == "quest.err.not_ready"
        assert (char.gold, char.xp) == (gold + 80, xp + 300)


async def test_a_mission_that_is_not_finished_cannot_be_handed_in():
    cid = await new_character()
    rng = random.Random(4)
    async with session_scope() as s:
        char = await get_char(s, cid)
        await quests.ensure_progress(s, char)
        prog = (await quests.progress(s, char))[TUSK]
        prog.stage, prog.state = "active", "active"  # the boar is still alive
        char.location = "broken_crown_tavern"
        out = await quests.turn_in(s, char, TUSK, ["bram"], rng)
        assert not out.ok and out.error == "quest.err.not_ready"
        assert (await quests.progress(s, char))[TUSK].state == "active"


async def test_a_milestone_reward_opens_the_level_in_the_same_transaction():
    """What the Collector's turn-in will do in B09: its reward carries the gate, and the level that
    the hero's XP had already paid for arrives with it, in one go."""
    cid = await new_character()
    rng = random.Random(5)
    async with session_scope() as s:
        char = await get_char(s, cid)
        characters.grant_xp(char, xp_for(10), Outcome())
        assert char.level == 9
        out = Outcome()
        await quests.apply_effects(s, char, [{"gold": 80}, {"milestone": ASH}], out, rng)
        assert char.gold >= 80 and char.level == 10
        assert characters.milestones_of(char) == [ASH]
        assert [e.key for e in out.events if e.key == "progress.level_up"]
