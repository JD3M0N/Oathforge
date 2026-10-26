import random

import pytest

from oathforge.database.session import session_scope
from oathforge.content import get_content
from oathforge.services import characters, exploration, world_map
from tests.services.helpers import get_char, new_character

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


async def test_leave_the_city_through_its_hub():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "broken_crown_tavern"
        road = world_map.route_to(char, "old_kings_road")  # unexplored, but the city's gate is always open
        assert road.via == ("crownreach_plaza",) and road.yards == 3200
        hub, roads = world_map.departures(char)
        assert hub == "crownreach_plaza" and {r.to for r in roads} == {"old_kings_road", "tusk_meadow"}
        assert world_map.route_to(char, "whispering_woods") is None  # never been there
        out = await exploration.travel(s, char, "old_kings_road", Calm(0))
        assert out.ok and char.location == "old_kings_road"
        char.location = "crownreach_plaza"
        assert world_map.route_to(char, "tusk_meadow").minutes == 20


class Calm(random.Random):
    """No ambush on the way."""

    def random(self):
        return 0.99


@pytest.mark.usefixtures("ruins")
async def test_new_places_one_stretch_at_a_time_known_ones_in_one_tap():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "old_kings_road"
        assert world_map.route_to(char, "elderwood_grove") is None
        far = {r.to: r for r in world_map.beyond(char)}
        assert far["elderwood_grove"].minutes == 60 and far["elderwood_grove"].via == ("whispering_woods",)
        assert "ruin_entrance" not in far  # another zone, and hidden
        for place in ("old_kings_road", "whispering_woods", "elderwood_grove"):
            characters.visited(char, place)
        assert "elderwood_grove" not in {r.to for r in world_map.beyond(char)}
        char.location = "crownreach_market"
        grove = world_map.route_to(char, "elderwood_grove")
        assert grove.via == ("crownreach_plaza", "old_kings_road", "whispering_woods")
        assert grove.danger == 2 and len(grove.stretches) == 4
        out = await exploration.travel(s, char, "elderwood_grove", Calm(0))
        assert out.ok and char.location == "elderwood_grove"
        assert out.events[0].key == "explore.arrived_via"


@pytest.mark.usefixtures("ruins")
async def test_cleared_ruin_back_to_town_in_one_tap():
    c = get_content()
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        rooms = ["ruin_entrance", "ruin_hall", "ruin_gallery", "ruin_sanctum"]
        for place in ["crownreach_plaza", "old_kings_road", "whispering_woods", *rooms]:
            characters.visited(char, place)
        char.flags = {**char.flags, "ruins_unlocked": True}
        char.location = "ruin_sanctum"
        assert world_map.route_to(char, "crownreach_plaza") is None  # the guards of the hall still wait
        assert world_map.route_to(char, "ruin_gallery") is not None  # next door: you can walk into them
        char.flags = {**char.flags, **{fe.flag: True for r in rooms for fe in c.locations[r].fixed_encounters}}
        home = world_map.route_to(char, "crownreach_plaza")
        assert home.via == ("ruin_gallery", "ruin_hall", "ruin_entrance", "whispering_woods", "old_kings_road")


@pytest.mark.usefixtures("ruins")
async def test_hidden_route_and_yards():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "whispering_woods"
        assert world_map.route_to(char, "ruin_entrance") is None
        char.flags = {"ruins_unlocked": True}
        assert world_map.route_to(char, "ruin_entrance").yards == 2000
        char.location = "ruin_hall"
        gallery = world_map.route_to(char, "ruin_gallery")
        assert (gallery.minutes, gallery.yards) == (3, 150)  # knee-deep water


@pytest.mark.usefixtures("ruins")
def test_place_activities():
    tavern = dict(world_map.activities("broken_crown_tavern", ["bram"]))
    assert tavern["rest"] == {"cost": 5} and "craft" in tavern and "npc" in tavern
    market = [k for k, _ in world_map.activities("crownreach_market", ["mira", "tessa"])]
    assert market.count("shop") == 2
    assert [k for k, _ in world_map.activities("ironvein_mine", [])] == ["gather_mining", "hunt"]
    assert world_map.activities("ruin_ossuary", []) == [("rest_free", {"cost": 0})]
