"""Professions (two slots, swapping keeps XP), hobbies (no slot) and atomic crafting."""

import pytest
from sqlalchemy import select

from oathforge.database.models import Character, ItemInstance
from oathforge.database.session import session_scope
from oathforge.services import characters, crafting, inventory, professions
from oathforge.services.events import Outcome

pytestmark = pytest.mark.usefixtures("database")


async def new_character(location="crownreach_workshops") -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "soldier", "paladin")
        char.location = location
        return char.id


async def get_char(s, cid) -> Character:
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())


async def test_two_slots_and_swapping_keeps_xp():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.gold = 100
        assert (await professions.learn(s, char, "alchemy")).ok
        assert (await professions.learn(s, char, "alchemy")).error == "prof.err.already"
        assert (await professions.learn(s, char, "blacksmithing")).ok
        assert (await professions.learn(s, char, "scribing")).error == "prof.err.slots_full"
        professions.grant_xp(char, "alchemy", 90, Outcome())
        out = await professions.learn(s, char, "scribing", replace="alchemy")
        assert out.ok and professions.active(char) == ["scribing", "blacksmithing"]
        assert char.gold == 100 - professions.SWAP_COST
        assert professions.xp(char, "alchemy") == 90 and professions.rank(char, "alchemy") == 1  # not forgotten


async def test_learning_only_at_the_guild():
    cid = await new_character(location="crownreach_plaza")
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await professions.learn(s, char, "alchemy")).error == "prof.err.not_guild"


async def test_crafting_is_all_or_nothing():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await crafting.craft(s, char, "iron_ingot")).error == "craft.err.not_your_profession"
        await professions.learn(s, char, "blacksmithing")
        await inventory.add_item(s, char, "iron_ore", 3)  # but no coal
        out = await crafting.craft(s, char, "iron_ingot")
        assert out.error == "craft.err.missing"
        assert await inventory.count(s, char, "iron_ore") == 3  # nothing spent
        await inventory.add_item(s, char, "coal", 1)
        out = await crafting.craft(s, char, "iron_ingot")
        assert out.ok and await inventory.count(s, char, "iron_ingot") == 1
        assert await inventory.count(s, char, "iron_ore") == 0 and await inventory.count(s, char, "coal") == 0
        assert professions.xp(char, "blacksmithing") == 10
        assert (await crafting.craft(s, char, "iron_sword")).error == "craft.err.rank"


async def test_station_rank_and_crafted_by():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await inventory.add_item(s, char, "raw_meat", 2)
        await inventory.add_item(s, char, "bloodroot", 1)
        assert (await crafting.craft(s, char, "hunter_stew")).error == "craft.err.no_station"  # the hearth is at the tavern
        char.location = "broken_crown_tavern"
        assert "hunter_stew" in crafting.recipes_here(char)
        assert (await crafting.craft(s, char, "hunter_stew")).ok
        await professions.learn(s, char, "blacksmithing")  # learned elsewhere: refused
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.location = "crownreach_workshops"
        await professions.learn(s, char, "blacksmithing")
        professions.grant_xp(char, "blacksmithing", 240, Outcome())
        await inventory.add_item(s, char, "iron_ingot", 2)
        await inventory.add_item(s, char, "oak_plank", 1)
        assert (await crafting.craft(s, char, "iron_sword")).ok
        sword = await s.scalar(select(ItemInstance).where(ItemInstance.item_key == "iron_sword"))
        assert sword.crafted_by == cid


async def test_low_rank_recipes_give_half_xp():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await professions.learn(s, char, "carpentry")
        char.professions = {"active": ["carpentry"], "xp": {"carpentry": 240}}  # rank 2
        await inventory.add_item(s, char, "oak_log", 3)
        await crafting.craft(s, char, "oak_plank")
        assert professions.xp(char, "carpentry") == 240 + 8 // 2
        assert await inventory.count(s, char, "oak_plank") == 2


async def test_cooking_is_a_hobby_without_a_slot():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await professions.learn(s, char, "cooking")).error == "prof.err.hobby"
        char.professions = {"active": ["cooking", "alchemy"], "xp": {"cooking": 30}}  # learned before v0.7.0
        assert professions.active(char) == ["alchemy"]  # the slot is free again
        assert "cooking" in professions.usable(char) and professions.xp(char, "cooking") == 30
        assert (await professions.learn(s, char, "artificing")).ok
        assert professions.active(char) == ["alchemy", "artificing"]


async def test_scribing_and_artificing_recipes():
    cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await professions.learn(s, char, "scribing")
        await professions.learn(s, char, "artificing")
        await inventory.add_item(s, char, "bloodroot", 1)
        await inventory.add_item(s, char, "coal", 3)
        await inventory.add_item(s, char, "boar_hide", 1)
        await inventory.add_item(s, char, "iron_ore", 1)
        await inventory.add_item(s, char, "plant_fiber", 3)
        for recipe in ("ink", "parchment", "scroll_firebolt", "black_powder", "fuse", "smoke_bomb"):
            assert (await crafting.craft(s, char, recipe)).ok, recipe
        assert await inventory.count(s, char, "scroll_firebolt") == 1
        assert await inventory.count(s, char, "smoke_bomb") == 1
        assert (await crafting.craft(s, char, "fire_bomb")).error == "craft.err.rank"
