import random

import pytest

from oathforge.database.session import session_scope
from oathforge.services import exploration, world_map
from tests.services.test_services import get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


async def test_city_walk_takes_the_shortest_way():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "broken_crown_tavern"
        route = world_map.route_to(char, "crownreach_workshops")
        assert (route.minutes, route.yards) == (7, 700)
        assert route.via == ("crownreach_plaza", "crownreach_market")
        out = await exploration.travel(s, char, "crownreach_chapel", random.Random(0))
        assert out.ok and char.location == "crownreach_chapel"
        assert out.events[0].params["yards"] == 400


async def test_leave_the_city_only_from_its_hub():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "broken_crown_tavern"
        assert world_map.route_to(char, "old_kings_road") is None
        hub, roads = world_map.departures(char)
        assert hub == "crownreach_plaza" and {r.to for r in roads} == {"old_kings_road", "tusk_meadow"}
        out = await exploration.travel(s, char, "old_kings_road", random.Random(0))
        assert not out.ok and char.location == "broken_crown_tavern"
        char.location = "crownreach_plaza"
        assert world_map.route_to(char, "tusk_meadow").minutes == 20


async def test_wilds_and_dungeons_go_one_stretch_at_a_time():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "old_kings_road"
        assert world_map.route_to(char, "elderwood_grove") is None
        far = {r.to: r for r in world_map.beyond(char)}
        assert far["elderwood_grove"].minutes == 60 and far["elderwood_grove"].via == ("whispering_woods",)
        assert "crypt_entrance" not in far  # another zone, and hidden
        char.location = "crypt_entrance"
        assert world_map.route_to(char, "crypt_sanctum") is None
        assert world_map.beyond(char) == []
        assert {r.to for r in world_map.destinations(char)} == {"whispering_woods", "crypt_hall"}


async def test_hidden_route_and_yards():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "whispering_woods"
        assert world_map.route_to(char, "crypt_entrance") is None
        char.flags = {"crypt_unlocked": True}
        assert world_map.route_to(char, "crypt_entrance").yards == 2000
        char.location = "crypt_hall"
        gallery = world_map.route_to(char, "crypt_gallery")
        assert (gallery.minutes, gallery.yards) == (3, 150)  # knee-deep water


def test_place_activities():
    tavern = dict(world_map.activities("broken_crown_tavern", ["bram"]))
    assert tavern["rest"] == {"cost": 5} and "craft" in tavern and "npc" in tavern
    market = [k for k, _ in world_map.activities("crownreach_market", ["mira", "tessa"])]
    assert market.count("shop") == 2
    assert [k for k, _ in world_map.activities("ironvein_mine", [])] == ["gather_mining", "hunt"]
    assert world_map.activities("crypt_ossuary", []) == [("rest_free", {"cost": 0})]
