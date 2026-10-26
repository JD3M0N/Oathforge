"""Travel, ambushes, flags, discoveries, free checks, rest, the chapel and the clock."""

import random

import pytest

from oathforge.database.session import session_scope
from oathforge.engine import timings
from oathforge.services import characters, combat_service, exploration, world_map
from oathforge.services.events import Outcome
from tests.services.helpers import get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


# ---------------------------------------------------------------- exploration


@pytest.mark.usefixtures("ruins")
async def test_travel_only_along_routes():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out = await exploration.travel(s, char, "ruin_sanctum", random.Random(0))
        assert not out.ok and char.location == "crownreach_plaza"
        out = await exploration.travel(s, char, "broken_crown_tavern", random.Random(0))
        assert out.ok and char.location == "broken_crown_tavern"


class Ambush(random.Random):
    """Every roll on the way says «ambush» and picks the first choice."""

    def random(self):
        return 0.0


async def test_a_trip_rolls_one_ambush_and_carries_on():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        for place in ("old_kings_road", "whispering_woods"):
            characters.visited(char, place)
        assert exploration.trip_chance(world_map.route_to(char, "old_kings_road")) == pytest.approx(0.15)
        assert exploration.trip_chance(world_map.route_to(char, "whispering_woods")) == pytest.approx(0.35)
        out = await exploration.travel(s, char, "whispering_woods", Ambush(1))
        assert out.ok and char.location == "old_kings_road" and char.state == "in_combat"
        assert out.events[0].key == "explore.trip_stopped"
        assert char.flags["trip"] == {"to": "whispering_woods", "rolled": True}
        char.state = "idle"  # the fight is over
        assert exploration.trip(char) == "whispering_woods"
        out = await exploration.travel(s, char, "whispering_woods", Ambush(1))  # no second roll
        assert out.ok and char.location == "whispering_woods" and char.state == "idle"
        assert "trip" not in char.flags


async def test_defeat_ends_the_trip():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.flags = {**char.flags, "trip": {"to": "whispering_woods", "rolled": True}}
        await characters.defeat_penalty(char, Outcome())
        assert "trip" not in char.flags


@pytest.mark.usefixtures("ruins")
async def test_locked_route_needs_flag():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "whispering_woods"
        assert "ruin_entrance" not in [e.to for e in exploration.exits(char)]
        char.flags = {"ruins_unlocked": True}
        assert "ruin_entrance" in [e.to for e in exploration.exits(char)]


@pytest.mark.usefixtures("ruins")
async def test_fixed_encounter_triggers_once():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.flags = "whispering_woods", {"ruins_unlocked": True}
        out = await exploration.travel(s, char, "ruin_entrance", random.Random(1))
        assert out.encounter_id and char.state in ("in_combat", "idle")
        enc = await combat_service.active_encounter(s, char)
        if enc:
            assert enc.fixed_flag == "cleared_ruin_entrance"


@pytest.mark.usefixtures("ruins")
async def test_investigate_finds_discovery_once():
    _, cid = await new_character(cls="rogue", bg="scholar")
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "ruin_ossuary"
        gold0 = char.gold
        for seed in range(40):
            char.checks_tried = {}  # a new day: failed secrets can be tried again
            await exploration.investigate(s, char, random.Random(seed))
        assert char.flags.get("found_ossuary_coins") and char.flags.get("warden_lore")
        assert char.gold == gold0 + 25
        out = await exploration.investigate(s, char, random.Random(0))
        assert out.events[0].key == "explore.nothing_more"


class AlwaysOne(random.Random):
    def randint(self, a, b):
        return a


@pytest.mark.usefixtures("ruins")
async def test_failed_investigation_waits_for_tomorrow(monkeypatch):
    _, cid = await new_character(cls="rogue", bg="scholar")
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "ruin_ossuary"
        out = await exploration.investigate(s, char, AlwaysOne())
        assert out.events[-1].key == "explore.found_nothing"
        assert (await exploration.investigate(s, char, random.Random(0))).events[0].key == "explore.already_tried"
        tomorrow = exploration.time.time() + exploration.GAME_DAY_SECONDS
        monkeypatch.setattr(exploration.time, "time", lambda: tomorrow)
        assert (await exploration.investigate(s, char, AlwaysOne())).events[0].key == "check.result"


async def test_free_check_once_per_skill_place_and_day(monkeypatch):
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        out, _ = await exploration.check_skill(s, char, "investigation", "medium", random.Random(0))
        assert out.ok and out.events[0].key == "check.result"
        out, ok = await exploration.check_skill(s, char, "investigation", "medium", random.Random(0))
        assert not out.ok and out.error == "check.already_tried" and not ok
        # another skill, or the same skill somewhere else, is a new attempt
        assert (await exploration.check_skill(s, char, "perception", "medium", random.Random(0)))[0].ok
        char.location = "broken_crown_tavern"
        assert (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        assert not (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        # levelling up lets you try again
        char.level += 1
        assert (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        # so does a new day, which also forgets older attempts
        tomorrow = exploration.time.time() + exploration.GAME_DAY_SECONDS
        monkeypatch.setattr(exploration.time, "time", lambda: tomorrow)
        assert (await exploration.check_skill(s, char, "investigation", "medium", random.Random(0)))[0].ok
        assert list(char.checks_tried) == ["free:investigation:broken_crown_tavern"]


async def test_long_rest_takes_its_time_asleep_then_restores():
    from oathforge.services import activities

    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.hp = "broken_crown_tavern", 1
        characters.set_pool(char, 0)  # the bar is spent
        char.conditions = {"injured": True}
        out = await activities.start(s, char, "rest", "rest", now=1000)
        assert out.ok and char.gold == 10 and char.state == "busy" and char.hp == 1  # paid, asleep, not healed yet
        assert (await exploration.travel(s, char, "crownreach_plaza", random.Random(0))).error == "activity.err.busy"
        assert (await activities.claim(s, char, now=1000 + timings.REST_SECONDS - 60)).error == "activity.err.not_ready"
        out = await activities.claim(s, char, now=1000 + timings.REST_SECONDS)
        assert out.ok and char.state == "idle" and char.hp == char.max_hp
        assert characters.pool_of(char) == characters.resource_max(char) > 0 and "injured" not in char.conditions


async def test_abandoned_rest_heals_nothing_and_keeps_the_gold():
    from oathforge.services import activities

    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location, char.hp = "broken_crown_tavern", 1
        await activities.start(s, char, "rest", "rest", now=1000)
        assert (await activities.cancel(s, char, now=1060)).ok
        assert char.hp == 1 and char.gold == 10 and char.state == "idle"


async def test_chapel_cures_wounds_for_a_fee_and_closes_grave_ones():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "crownreach_chapel"
        assert (await exploration.cure_wounds(s, char, random.Random(0))).error == "inv.err.full_hp"
        char.hp = 1
        out = await exploration.cure_wounds(s, char, random.Random(0))
        assert out.ok and char.gold == 12 and char.hp == char.max_hp  # the fee (3 gold), and complete
        # after a defeat: injured and broke, Ysolde still helps (for what you have: nothing) and closes the grave wounds
        char.hp, char.gold, char.conditions = 1, 0, {"injured": True}
        out = await exploration.cure_wounds(s, char, random.Random(0))
        assert out.ok and "injured" not in char.conditions and "explore.healed_injured" in [e.key for e in out.events]
        char.hp = char.max_hp // 2
        char.conditions = {"injured": True}  # even at the half-HP cap, she can close them
        assert (await exploration.cure_wounds(s, char, random.Random(0))).ok and "injured" not in char.conditions
        char.location = "crownreach_plaza"
        assert (await exploration.cure_wounds(s, char, random.Random(0))).error == "explore.err.no_healer"


def test_day_night_clock():
    assert exploration.game_hour(0) == 0 and exploration.is_night(0)
    assert not exploration.is_night(exploration.GAME_DAY_SECONDS / 2)
    hour = exploration.GAME_DAY_SECONDS / 24  # ten real minutes
    assert exploration.clock(0) == "00:00" and exploration.clock(14.5 * hour) == "14:30"
    assert exploration.until_switch(0) == 60  # midnight: dawn at 06:00, six game hours away
    assert exploration.until_switch(19 * hour) == 10  # dusk at 20:00
    assert exploration.until_switch(23 * hour) == 70  # night: dawn tomorrow
