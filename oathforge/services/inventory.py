"""Items, equipment, consumables and shops.

Rows are locked with SELECT ... FOR UPDATE so two concurrent actions cannot
spend the same potion or the same coin.
"""

import math
import random
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.content.schemas import RestoreHp, RestoreSpellCharge
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
    if char.level < item.min_level and not inst.equipped_slot:  # T1 gear is forged by rank and worn by level
        return Outcome.refused("inv.err.level", level=item.min_level)
    if inst.equipped_slot:
        inst.equipped_slot = None
        return Outcome().add("inv.unequipped", item=item.name.model_dump())
    for other in await items_of(session, char, lock=True):
        if other.equipped_slot == item.slot:
            other.equipped_slot = None
    inst.equipped_slot = item.slot
    return Outcome().add("inv.equipped", item=item.name.model_dump())


async def combat_items(session: AsyncSession, char: Character) -> dict[str, int]:
    """What the combat panel can use: healing potions, scrolls and bombs carried."""
    c = get_content()
    out: dict[str, int] = {}
    for inst in await items_of(session, char):
        item = c.items.get(inst.item_key)
        if item is not None and (inst.item_key == "healing_potion" or item.combat is not None):
            out[inst.item_key] = out.get(inst.item_key, 0) + inst.qty
    return out


async def consume_healing(session: AsyncSession, char: Character, key: str, rng: random.Random) -> int | None:
    """Spend one consumable and return the rolled healing, or None if unavailable."""
    item = get_content().items.get(key)
    if item is None or item.heal is None:
        return None
    if not await remove_item(session, char, key, 1):
        return None
    return roll(item.heal, rng).total


def effects_of(item) -> list:
    """What "Use" does outside combat; a plain ``heal`` counts as a restore_hp effect."""
    if item.heal and not any(isinstance(e, RestoreHp) for e in item.effects):
        return [RestoreHp(type="restore_hp", dice=item.heal), *item.effects]
    return list(item.effects)


def spent_abilities(char: Character, spells_only: bool) -> list[tuple[str, int]]:
    """(ability, uses missing) for limited abilities below their maximum, most spent first.
    Spells are the limited abilities of a class that casts (priest, mage, druid, bard, warlock)."""
    cls = get_content().classes[char.class_key]
    if spells_only and not cls.casting:
        return []
    out = []
    for key, a in cls.abilities.items():
        left = char.resources.get(key)
        if a.uses and a.level <= char.level and a.kind != "passive" and left is not None and left < a.uses:
            out.append((key, a.uses - left))
    return sorted(out, key=lambda kv: -kv[1])


def spell_choices(char: Character, item) -> list[str]:
    """The spent spells a spell-restoring item could bring back (empty for any other item)."""
    if not any(isinstance(e, RestoreSpellCharge) for e in effects_of(item)):
        return []
    return [k for k, _ in spent_abilities(char, spells_only=True)]


def _restore_use(char: Character, key: str, amount: int, out: Outcome) -> None:
    a = get_content().classes[char.class_key].abilities[key]
    char.resources = {**char.resources, key: min(a.uses, char.resources[key] + amount)}
    out.add("inv.use_restored", ability=a.name.model_dump(), uses=char.resources[key], max=a.uses)


def _refusal(char: Character, effect, now: float) -> str | None:
    """Why this effect would do nothing now (then the item is not spent), or None."""
    if isinstance(effect, RestoreHp):
        return "inv.err.full_hp" if char.hp >= hp_cap(char) else None
    if isinstance(effect, RestoreSpellCharge):
        return "inv.err.no_spent_spell" if not spent_abilities(char, spells_only=True) else None
    if (char.cooldowns or {}).get("short_rest", 0) > now:
        return "inv.err.cooldown"
    if char.hp >= hp_cap(char) and not spent_abilities(char, spells_only=False):
        return "inv.err.no_need"
    return None


async def use_item_outside_combat(session: AsyncSession, char: Character, key: str, rng: random.Random,
                                  now: float | None = None, ability: str | None = None) -> Outcome:
    """Use a consumable. ``ability``: which spent spell a mana potion brings back (default: the most spent)."""
    item = get_content().items.get(key)
    effects = effects_of(item) if item else []
    if not effects:
        return Outcome.refused("inv.err.not_usable")
    if char.level < item.min_level:
        return Outcome.refused("inv.err.level", level=item.min_level)
    now = time.time() if now is None else now
    useful = [e for e in effects if _refusal(char, e, now) is None]
    if not useful:
        reason = _refusal(char, effects[0], now)
        if reason == "inv.err.cooldown":
            ready = (char.cooldowns or {}).get("short_rest", now)
            return Outcome.refused(reason, minutes=math.ceil((ready - now) / 60))
        return Outcome.refused(reason)
    if not await remove_item(session, char, key, 1):
        return Outcome.refused("inv.err.not_found")
    out = Outcome()
    name = item.name.model_dump()
    for effect in useful:
        before = char.hp
        if isinstance(effect, RestoreHp):
            char.hp = min(hp_cap(char), char.hp + roll(effect.dice, rng).total)
            out.add("inv.healed", item=name, amount=char.hp - before, hp=char.hp, max_hp=char.max_hp)
        elif isinstance(effect, RestoreSpellCharge):
            out.add("inv.used", item=name)
            spent = [k for k, _ in spent_abilities(char, spells_only=True)]
            _restore_use(char, ability if ability in spent else spent[0], effect.amount, out)
        else:  # short rest: part of the HP, a use back, then the cooldown; never lifts "injured"
            out.add("inv.short_rest", item=name)
            char.hp = min(hp_cap(char), char.hp + max(1, round(char.max_hp * effect.hp_percent)))
            if char.hp > before:
                out.add("inv.healed_hp", amount=char.hp - before, hp=char.hp, max_hp=char.max_hp)
            spent = spent_abilities(char, spells_only=False)
            if spent:
                _restore_use(char, spent[0][0], effect.charges, out)
            char.cooldowns = {**(char.cooldowns or {}), "short_rest": now + effect.cooldown_seconds}
    return out


# ---------------------------------------------------------------- shops

def buy_price(item_key: str, reputation: int) -> int:
    """Shops charge up to 25% more or less depending on reputation (-100..100)."""
    base = get_content().items[item_key].value
    return max(1, round(base * (1 - reputation / 400)))


def sell_price(item_key: str, reputation: int) -> int:
    """Half the value (up to 25% better with reputation); anything worth a coin sells for at least one."""
    base = get_content().items[item_key].value
    return max(1 if base >= 1 else 0, round(base * 0.5 * (1 + reputation / 400)))


async def buy(session: AsyncSession, char: Character, npc_key: str, item_key: str, reputation: int) -> Outcome:
    npc = get_content().npcs[npc_key]
    if not npc.shop or item_key not in npc.shop.items:
        return Outcome.refused("shop.err.not_sold")
    price = buy_price(item_key, reputation)
    if char.gold < price:
        return Outcome.refused("shop.err.no_gold", price=price)
    char.gold -= price
    await add_item(session, char, item_key, 1)
    return Outcome().add("shop.bought", item=get_content().items[item_key].labelled(), price=price,
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
    return Outcome().add("shop.sold", item=item.labelled(), price=price, gold=char.gold)
