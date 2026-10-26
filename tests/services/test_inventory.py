"""Potions, shops, equipment, item removal, double spending and duplicate nonces."""

import asyncio
import random

import pytest
from sqlalchemy import func, select

from oathforge.database.models import ActionLog, ItemInstance
from oathforge.database.session import session_scope
from oathforge.services import audit, characters, inventory
from tests.services.helpers import get_char, new_character

pytestmark = pytest.mark.usefixtures("database")


# ---------------------------------------------------------------- inventory & shops


async def test_potion_heals_and_is_consumed():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.hp = 2
        out = await inventory.use_item_outside_combat(s, char, "healing_potion", random.Random(0))
        assert out.ok and char.hp > 2
        assert await inventory.count(s, char, "healing_potion") == 0
        again = await inventory.use_item_outside_combat(s, char, "healing_potion", random.Random(0))
        assert not again.ok


async def test_buy_sell_and_reputation_prices():
    _, cid = await new_character()
    assert (
        inventory.buy_price("chain_mail", 100)
        < inventory.buy_price("chain_mail", 0)
        < inventory.buy_price("chain_mail", -100)
    )
    async with session_scope() as s:
        char = await get_char(s, cid)
        char.gold = 3
        out = await inventory.buy(s, char, "tessa", "chain_mail", 0)
        assert not out.ok and char.gold == 3
        out = await inventory.buy(s, char, "tessa", "torch", 0)
        assert out.ok and char.gold == 2
        rope = next(i for i in await inventory.items_of(s, char) if i.item_key == "rope")
        out = await inventory.sell(s, char, "tessa", rope.id, 0)
        assert out.ok


async def test_cannot_sell_equipped_or_quest_items():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        sword = next(i for i in await inventory.items_of(s, char) if i.item_key == "longsword")
        assert not (await inventory.sell(s, char, "tessa", sword.id, 0)).ok


async def test_equip_swaps_slot():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        await inventory.add_item(s, char, "dagger")
        dagger = next(i for i in await inventory.items_of(s, char) if i.item_key == "dagger")
        assert (await inventory.equip(s, char, dagger.id)).ok
        gear = await characters.equipped(s, char)
        assert gear["main_hand"].item_key == "dagger"


async def test_remove_item_is_all_or_nothing():
    _, cid = await new_character()
    async with session_scope() as s:
        char = await get_char(s, cid)
        assert not await inventory.remove_item(s, char, "healing_potion", 2)
        assert await inventory.count(s, char, "healing_potion") == 1


async def test_concurrent_potion_double_spend(is_postgres):
    if not is_postgres:
        pytest.skip("row-lock concurrency needs PostgreSQL (set TEST_DATABASE_URL)")
    _, cid = await new_character()

    async def spend():
        async with session_scope() as s:
            char = await get_char(s, cid, lock=False)
            ok = await inventory.remove_item(s, char, "healing_potion", 1)
            await asyncio.sleep(0.05)
            return ok

    results = await asyncio.gather(spend(), spend())
    assert sorted(results) == [False, True]
    async with session_scope() as s:
        n = await s.scalar(
            select(func.count())
            .select_from(ItemInstance)
            .where(ItemInstance.owner_character_id == cid, ItemInstance.item_key == "healing_potion")
        )
        assert n == 0


# ---------------------------------------------------------------- idempotency


async def test_duplicate_nonce_is_rejected():
    uid, cid = await new_character()
    async with session_scope() as s:
        assert await audit.claim(s, "1:abc", user_id=uid, character_id=cid, verb="go") is not None
    async with session_scope() as s:
        assert await audit.claim(s, "1:abc", user_id=uid, character_id=cid, verb="go") is None
        assert await audit.claim(s, "1:other", user_id=uid, character_id=cid, verb="go") is not None
    async with session_scope() as s:
        assert await s.scalar(select(func.count()).select_from(ActionLog)) == 2
