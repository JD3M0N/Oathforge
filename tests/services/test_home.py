"""Your room at the guild: the starter recipes that furnish it, the free rest and the chest."""

import pytest
from sqlalchemy import select

from oathforge.config import get_settings
from oathforge.database.models import Character, ItemInstance
from oathforge.database.session import session_scope
from oathforge.services import activities, characters, crafting, home, inventory, quests
from oathforge.services.events import Outcome

pytestmark = pytest.mark.usefixtures("database")

GUILD = "adventurers_guild"


async def new_character(location=GUILD) -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        char.location = location
        return char.id


async def get_char(s, cid) -> Character:
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())


async def furnish(s, char) -> None:
    """What the mission does: both pieces installed."""
    home.install(char, "chest", Outcome())
    home.install(char, "bed", Outcome())


async def test_the_starter_recipes_only_work_during_their_mission():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await inventory.add_item(s, char, "oak_plank", 6)
        await inventory.add_item(s, char, "guild_cloth", 1)
        # the mission has not started: no trade, and no recipe either
        assert "starter_chest" not in crafting.recipes_here(char)
        assert (await crafting.craft(s, char, "starter_chest")).error == "craft.err.quest_only"
    async with session_scope() as s:  # with the mission running, both pieces go up, once each
        char = await get_char(s, cid)
        prog = await quests.progress(s, char, lock=True)
        prog["tut_room"].state, prog["tut_room"].stage = "active", "active"
        await s.flush()
        assert "starter_chest" in crafting.recipes_here(char, {"tut_room"})
        assert (await crafting.craft(s, char, "starter_chest")).ok
        assert home.chest_level(char) == 1 and home.capacity(char) == get_settings().chest_slots
        assert await inventory.count(s, char, "oak_plank") == 2
        assert (await crafting.craft(s, char, "starter_bed")).ok
        assert home.has_bed(char) and await inventory.count(s, char, "guild_cloth") == 0
        # a starter recipe is never made in batches
        await inventory.add_item(s, char, "oak_plank", 8)
        assert (await crafting.craft(s, char, "starter_chest", qty=2)).error == "craft.err.qty"


async def test_the_bed_makes_resting_free():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert activities.rest_cost(char) is None  # a guild hall is no inn
        assert (await activities.check(s, char, "rest", "rest")).error == "explore.err.no_rest"
        await furnish(s, char)
        assert activities.rest_cost(char) == 0
        assert await activities.check(s, char, "rest", "rest") is None
        char.gold = 0
        out = await activities.start(s, char, "rest", "rest")
        assert out.ok and char.gold == 0  # not a coin for your own bed


async def test_the_chest_moves_items_without_copying_them():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await inventory.add_item(s, char, "iron_ore", 10)
        assert (await home.deposit(s, char, "iron_ore", 3)).error == "home.err.no_chest"
        await furnish(s, char)
        assert (await home.deposit(s, char, "iron_ore", 30)).error == "home.err.not_enough"
        assert await inventory.count(s, char, "iron_ore") == 10  # nothing moved
        assert (await home.deposit(s, char, "iron_ore", 4)).ok
        assert await inventory.count(s, char, "iron_ore") == 6
        assert await inventory.count(s, char, "iron_ore", container=inventory.CHEST) == 4
        total = await s.scalar(select(ItemInstance.qty).where(ItemInstance.item_key == "iron_ore",
                                                              ItemInstance.container == "chest"))
        assert total == 4  # one row in the chest, not a copy of the stack
        assert (await home.withdraw(s, char, "iron_ore", 10)).error == "home.err.not_stored"
        assert (await home.withdraw(s, char, "iron_ore", 4)).ok
        assert await inventory.count(s, char, "iron_ore") == 10
        assert await inventory.count(s, char, "iron_ore", container=inventory.CHEST) == 0
        rows = [i for i in await inventory.items_of(s, char) if i.item_key == "iron_ore"]
        assert len(rows) == 1  # back as one line


async def test_what_the_chest_keeps_is_out_of_reach_and_does_not_fit_forever():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await furnish(s, char)
        await inventory.add_item(s, char, "iron_sword", 1)  # not stackable: one slot each
        await inventory.add_item(s, char, "oak_plank", 2)
        assert (await home.deposit(s, char, "iron_sword", 1)).ok
        # stored items are not in the bag: they cannot be spent, sold or crafted with
        assert await inventory.count(s, char, "iron_sword") == 0
        assert not await inventory.remove_item(s, char, "iron_sword", 1)
        char.home = {**char.home, "chest": 1}
        char.location = "crownreach_plaza"
        assert (await home.deposit(s, char, "oak_plank", 1)).error == "home.err.away"
        assert (await home.withdraw(s, char, "iron_sword", 1)).error == "home.err.away"


async def test_an_upgrade_adds_room_without_losing_what_is_inside():
    cid = await new_character()
    settings = get_settings()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await furnish(s, char)
        await inventory.add_item(s, char, "iron_ore", 5)
        assert (await home.deposit(s, char, "iron_ore", 5)).ok
        home.install(char, "chest", Outcome())  # the carpentry upgrade
        assert home.chest_level(char) == 2
        assert home.capacity(char) == settings.chest_slots + settings.chest_slots_per_upgrade
        assert await inventory.count(s, char, "iron_ore", container=inventory.CHEST) == 5
