"""Items, equipment, consumables and shops.

Rows are locked with SELECT ... FOR UPDATE so two concurrent actions cannot
spend the same potion or the same coin.
"""

import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.database.models import Character, ItemInstance
from oathforge.engine.dice import roll
from oathforge.services.events import Outcome


def hp_cap(char: Character) -> int:
    """While injured (after a defeat) a character cannot heal past half HP until resting."""
    return char.max_hp // 2 if char.conditions.get("injured") else char.max_hp


async def items_of(session: AsyncSession, char: Character, lock: bool = False) -> list[ItemInstance]:
    stmt = select(ItemInstance).where(ItemInstance.owner_character_id == char.id).order_by(ItemInstance.id)
    if lock:
        stmt = stmt.with_for_update()
    return list(await session.scalars(stmt))


async def count(session: AsyncSession, char: Character, key: str) -> int:
    return sum(i.qty for i in await items_of(session, char) if i.item_key == key)


async def add_item(session: AsyncSession, char: Character, key: str, qty: int = 1,
                   crafted_by: int | None = None) -> None:
    item = get_content().items[key]
    if item.stackable:
        stmt = (select(ItemInstance)
                .where(ItemInstance.owner_character_id == char.id, ItemInstance.item_key == key)
                .with_for_update())
        existing = await session.scalar(stmt)
        if existing:
            existing.qty += qty
            return
        session.add(ItemInstance(owner_character_id=char.id, item_key=key, qty=qty, history=[]))
    else:
        for _ in range(qty):
            session.add(ItemInstance(owner_character_id=char.id, item_key=key, qty=1, crafted_by=crafted_by,
                                     history=[]))
    await session.flush()


async def remove_item(session: AsyncSession, char: Character, key: str, qty: int = 1) -> bool:
    """Remove ``qty`` of ``key``. All-or-nothing; returns False if not enough."""
    stmt = (select(ItemInstance)
            .where(ItemInstance.owner_character_id == char.id, ItemInstance.item_key == key)
            .order_by(ItemInstance.equipped_slot.is_not(None), ItemInstance.id)
            .with_for_update())
    rows = list(await session.scalars(stmt))
    if sum(r.qty for r in rows) < qty:
        return False
    for r in rows:
        if qty <= 0:
            break
        take = min(r.qty, qty)
        r.qty -= take
        qty -= take
        if r.qty == 0:
            await session.delete(r)
    await session.flush()
    return True


async def _own_instance(session: AsyncSession, char: Character, instance_id: int) -> ItemInstance | None:
    return await session.scalar(
        select(ItemInstance)
        .where(ItemInstance.id == instance_id, ItemInstance.owner_character_id == char.id)
        .with_for_update()
    )


async def equip(session: AsyncSession, char: Character, instance_id: int) -> Outcome:
    if char.state == "in_combat":
        return Outcome.refused("inv.err.in_combat")
    inst = await _own_instance(session, char, instance_id)
    if inst is None:
        return Outcome.refused("inv.err.not_found")
    item = get_content().items[inst.item_key]
    if item.slot is None:
        return Outcome.refused("inv.err.not_equippable")
    if inst.equipped_slot:
        inst.equipped_slot = None
        return Outcome().add("inv.unequipped", item=item.name.model_dump())
    for other in await items_of(session, char, lock=True):
        if other.equipped_slot == item.slot:
            other.equipped_slot = None
    inst.equipped_slot = item.slot
    return Outcome().add("inv.equipped", item=item.name.model_dump())


async def consume_healing(session: AsyncSession, char: Character, key: str, rng: random.Random) -> int | None:
    """Spend one consumable and return the rolled healing, or None if unavailable."""
    item = get_content().items.get(key)
    if item is None or item.heal is None:
        return None
    if not await remove_item(session, char, key, 1):
        return None
    return roll(item.heal, rng).total


async def use_item_outside_combat(session: AsyncSession, char: Character, key: str, rng: random.Random) -> Outcome:
    item = get_content().items.get(key)
    if item is None or item.heal is None:
        return Outcome.refused("inv.err.not_usable")
    if char.hp >= hp_cap(char):
        return Outcome.refused("inv.err.full_hp")
    amount = await consume_healing(session, char, key, rng)
    if amount is None:
        return Outcome.refused("inv.err.not_found")
    before = char.hp
    char.hp = min(hp_cap(char), char.hp + amount)
    return Outcome().add("inv.healed", item=item.name.model_dump(), amount=char.hp - before, hp=char.hp,
                         max_hp=char.max_hp)


# ---------------------------------------------------------------- shops

def buy_price(item_key: str, reputation: int) -> int:
    """Shops charge up to 25% more or less depending on reputation (-100..100)."""
    base = get_content().items[item_key].value
    return max(1, round(base * (1 - reputation / 400)))


def sell_price(item_key: str, reputation: int) -> int:
    base = get_content().items[item_key].value
    return max(0, round(base * 0.5 * (1 + reputation / 400)))


async def buy(session: AsyncSession, char: Character, npc_key: str, item_key: str, reputation: int) -> Outcome:
    npc = get_content().npcs[npc_key]
    if not npc.shop or item_key not in npc.shop.items:
        return Outcome.refused("shop.err.not_sold")
    price = buy_price(item_key, reputation)
    if char.gold < price:
        return Outcome.refused("shop.err.no_gold", price=price)
    char.gold -= price
    await add_item(session, char, item_key, 1)
    return Outcome().add("shop.bought", item=get_content().items[item_key].name.model_dump(), price=price,
                         gold=char.gold)


async def sell(session: AsyncSession, char: Character, npc_key: str, instance_id: int, reputation: int) -> Outcome:
    npc = get_content().npcs[npc_key]
    if not npc.shop or not npc.shop.buys:
        return Outcome.refused("shop.err.no_buy")
    inst = await _own_instance(session, char, instance_id)
    if inst is None:
        return Outcome.refused("inv.err.not_found")
    item = get_content().items[inst.item_key]
    if not item.sellable or inst.equipped_slot:
        return Outcome.refused("shop.err.cant_sell")
    price = sell_price(inst.item_key, reputation)
    if inst.qty > 1:
        inst.qty -= 1
    else:
        await session.delete(inst)
    char.gold += price
    return Outcome().add("shop.sold", item=item.name.model_dump(), price=price, gold=char.gold)
