"""Your room at the Adventurers' Guild: the bed you rest in for free and the chest that keeps your things.

The chest is a second container of the same item rows (``ItemInstance.container``), so nothing is copied:
depositing and withdrawing move the very same instance, with its ``crafted_by`` and its history.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.config import get_settings
from oathforge.content import get_content
from oathforge.database.models import Character, ItemInstance
from oathforge.services import characters, inventory, quests
from oathforge.services.events import Outcome


def has_bed(char: Character) -> bool:
    return bool((char.home or {}).get("bed"))


def chest_level(char: Character) -> int:
    """0 while there is no chest; 1 once it is built, and one more per upgrade."""
    return int((char.home or {}).get("chest", 0))


def capacity(char: Character) -> int:
    settings = get_settings()
    level = chest_level(char)
    return 0 if not level else settings.chest_slots + settings.chest_slots_per_upgrade * (level - 1)


def at_home(char: Character) -> bool:
    """Standing where your room is: the guild hall that granted it."""
    return get_content().locations[char.location].home and bool(char.home)


def install(char: Character, what: str, out: Outcome) -> None:
    """Put the furniture in the room. Building a second chest is an upgrade, not a second chest."""
    home = dict(char.home or {})
    if what == "bed":
        home["bed"] = True
    else:
        home["chest"] = int(home.get("chest", 0)) + 1
    char.home = home
    out.add(f"home.installed_{what}", capacity=capacity(char))


async def stored(session: AsyncSession, char: Character) -> list[ItemInstance]:
    return await inventory.items_of(session, char, container=inventory.CHEST)


async def deposit(session: AsyncSession, char: Character, key: str, qty: int = 1) -> Outcome:
    """Move items from the backpack into the chest, all of them or none."""
    if refusal := _closed(char):
        return refusal
    c = get_content()
    if key not in c.items:
        return Outcome.refused("inv.err.not_found")
    rows = [i for i in await inventory.items_of(session, char, lock=True) if i.item_key == key]
    free = [i for i in rows if not i.equipped_slot]
    if sum(i.qty for i in free) < qty:
        return Outcome.refused("home.err.not_enough", item=c.items[key].labelled())
    there = await stored(session, char)
    stack = next((i for i in there if i.item_key == key and c.items[key].stackable), None)
    if stack is None and len(there) + _instances_needed(key, qty) > capacity(char):
        return Outcome.refused("home.err.full", capacity=capacity(char))
    left = qty
    for row in free:
        if left <= 0:
            break
        take = min(row.qty, left)
        left -= take
        if take == row.qty:  # the whole row moves: it keeps its id, its crafted_by and its history
            if stack is not None and row.item_key == stack.item_key and c.items[key].stackable:
                stack.qty += row.qty
                await session.delete(row)
            else:
                row.container = inventory.CHEST
                stack = row if c.items[key].stackable else stack
        else:  # part of a stack: split it
            row.qty -= take
            if stack is not None:
                stack.qty += take
            else:
                stack = ItemInstance(owner_character_id=char.id, item_key=key, qty=take,
                                     container=inventory.CHEST, history=[])
                session.add(stack)
    await session.flush()
    out = Outcome().add("home.deposited", item=c.items[key].labelled(), qty=qty,
                        used=len(await stored(session, char)), capacity=capacity(char))
    return out.extend(await quests.on_event(session, char, "stash", key, qty))


async def withdraw(session: AsyncSession, char: Character, key: str, qty: int = 1) -> Outcome:
    """Move items from the chest back into the backpack, all of them or none."""
    if refusal := _closed(char):
        return refusal
    c = get_content()
    if key not in c.items:
        return Outcome.refused("inv.err.not_found")
    rows = [i for i in await inventory.items_of(session, char, lock=True, container=inventory.CHEST)
            if i.item_key == key]
    if sum(i.qty for i in rows) < qty:
        return Outcome.refused("home.err.not_stored", item=c.items[key].labelled())
    left = qty
    for row in rows:
        if left <= 0:
            break
        take = min(row.qty, left)
        left -= take
        if take == row.qty:
            row.container = inventory.BACKPACK
        else:
            row.qty -= take
            session.add(ItemInstance(owner_character_id=char.id, item_key=key, qty=take, history=[]))
    await _merge_backpack_stacks(session, char, key)
    await session.flush()
    out = Outcome().add("home.withdrew", item=c.items[key].labelled(), qty=qty,
                        used=len(await stored(session, char)), capacity=capacity(char))
    return out.extend(await quests.on_event(session, char, "take", key, qty))


async def _merge_backpack_stacks(session: AsyncSession, char: Character, key: str) -> None:
    """A stackable item back in the bag is one line again, not two."""
    if not get_content().items[key].stackable:
        return
    rows = [i for i in await inventory.items_of(session, char, lock=True) if i.item_key == key]
    for extra in rows[1:]:
        rows[0].qty += extra.qty
        await session.delete(extra)


def _instances_needed(key: str, qty: int) -> int:
    """Slots a deposit takes: one for a stack, one per piece for what does not stack."""
    return 1 if get_content().items[key].stackable else qty


def _closed(char: Character) -> Outcome | None:
    if refusal := characters.ensure_free(char):
        return refusal
    if not chest_level(char):
        return Outcome.refused("home.err.no_chest")
    if not at_home(char):
        return Outcome.refused("home.err.away")
    return None
