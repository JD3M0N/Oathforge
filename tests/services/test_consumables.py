"""Typed consumable effects: healing, mana (a spent spell use) and the resting draught (short rest)."""

import random
import time

import pytest
from sqlalchemy import select

from oathforge.database.models import Character
from oathforge.database.session import session_scope
from oathforge.services import characters, inventory

pytestmark = pytest.mark.usefixtures("database")


async def new_character(cls="sorcerer", level=3, items=()) -> int:
    async with session_scope() as s:
        user = await characters.get_or_create_user(s, 1, "es")
        char = await characters.create_character(s, user, "Aldric", "human", "scholar", cls)
        char.level = level
        char.resources = characters.full_resources(cls, level)
        for item in items:
            await inventory.add_item(s, char, item)
        return char.id


async def get_char(s, cid) -> Character:
    return await s.scalar(select(Character).where(Character.id == cid).with_for_update())


async def use(s, char, key, now=None):
    return await inventory.use_item_outside_combat(s, char, key, random.Random(0), now)


async def test_mana_potion_needs_a_spent_spell_and_is_kept_otherwise():
    cid = await new_character(items=("mana_potion",))
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await use(s, char, "mana_potion")).error == "inv.err.no_spent_spell"
        assert await inventory.count(s, char, "mana_potion") == 1  # not spent
        char.resources = {**char.resources, "fireball": 0, "sleep": 2}
        out = await use(s, char, "mana_potion")
        assert out.ok and char.resources["fireball"] == 1 and char.resources["sleep"] == 2
        assert await inventory.count(s, char, "mana_potion") == 0


async def test_mana_potion_does_nothing_for_classes_without_spells():
    cid = await new_character(cls="warrior", level=2, items=("mana_potion",))
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.resources = {**char.resources, "second_wind": 0}
        assert (await use(s, char, "mana_potion")).error == "inv.err.no_spent_spell"


async def test_resting_draught_heals_a_fifth_restores_a_use_and_has_a_cooldown():
    cid = await new_character(cls="warrior", level=2, items=("rest_draught", "rest_draught"))
    now = time.time()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert (await use(s, char, "rest_draught", now)).error == "inv.err.no_need"  # rested: kept
        char.hp = 1
        char.resources = {**char.resources, "second_wind": 0}
        out = await use(s, char, "rest_draught", now)
        assert out.ok and char.hp == 1 + max(1, round(char.max_hp * 0.2)) and char.resources["second_wind"] == 1
        out = await use(s, char, "rest_draught", now + 60)
        assert out.error == "inv.err.cooldown" and await inventory.count(s, char, "rest_draught") == 1
        char.hp = 1
        assert (await use(s, char, "rest_draught", now + 4 * 3600 + 1)).ok


async def test_resting_draught_respects_the_injury_cap():
    cid = await new_character(cls="warrior", level=2, items=("rest_draught",))
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.max_hp = 40
        char.conditions = {"injured": True}
        char.hp = 19  # cap is 20
        assert (await use(s, char, "rest_draught")).ok
        assert char.hp == 20 and char.conditions.get("injured")


async def test_food_heals_through_the_old_heal_field():
    cid = await new_character(cls="warrior", level=1, items=("hunter_stew",))
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = 1
        out = await use(s, char, "hunter_stew")
        assert out.ok and char.hp > 1
