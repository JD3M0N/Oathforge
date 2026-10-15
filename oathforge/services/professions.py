"""Crafting professions: two active, learned and swapped at the guild (Craftsmen's Row).

Swapping keeps the XP of the profession you drop, so trying another one never wastes progress.
Hobbies (cooking, fishing) take no slot: everyone can practise them. Fishing has no station: it levels by fishing.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine import gathering
from oathforge.services import characters
from oathforge.services.events import Outcome

SLOTS = 2
SWAP_COST = 25  # gold, to replace an active profession


def is_hobby(key: str) -> bool:
    prof = get_content().professions.get(key)
    return prof is not None and prof.hobby


def active(char: Character) -> list[str]:
    """The professions in the two slots (a hobby learned before v0.7.0 no longer takes one)."""
    return [k for k in (char.professions or {}).get("active", []) if not is_hobby(k)]


def hobbies() -> list[str]:
    return [k for k, p in get_content().professions.items() if p.hobby]


def usable(char: Character) -> list[str]:
    """Professions you can craft with: your active ones plus every hobby."""
    return active(char) + hobbies()


def xp(char: Character, key: str) -> int:
    return int((char.professions or {}).get("xp", {}).get(key, 0))


def rank(char: Character, key: str) -> int:
    return gathering.rank_for(xp(char, key))


def _set(char: Character, active_list: list[str], xp_map: dict[str, int]) -> None:
    char.professions = {"active": active_list, "xp": xp_map}  # a new dict, so the JSON column notices


async def learn(session: AsyncSession, char: Character, key: str, replace: str | None = None) -> Outcome:
    """Learn ``key``: free while a slot is empty; with both full, ``replace`` one for SWAP_COST gold."""
    if refusal := characters.ensure_free(char):
        return refusal
    c = get_content()
    if not c.locations[char.location].guild:
        return Outcome.refused("prof.err.not_guild")
    if key not in c.professions:
        return Outcome.refused("prof.err.unknown")
    if c.professions[key].hobby:
        return Outcome.refused("prof.err.hobby", prof=c.professions[key].name.model_dump())
    current = active(char)
    if key in current:
        return Outcome.refused("prof.err.already", prof=c.professions[key].name.model_dump())
    xp_map = dict((char.professions or {}).get("xp", {}))
    name = c.professions[key].name.model_dump()
    if len(current) < SLOTS:
        _set(char, current + [key], xp_map)
        return Outcome().add("prof.learned", prof=name, used=len(current) + 1, slots=SLOTS)
    if replace not in current:
        return Outcome.refused("prof.err.slots_full", slots=SLOTS)
    if char.gold < SWAP_COST:
        return Outcome.refused("shop.err.no_gold", price=SWAP_COST)
    char.gold -= SWAP_COST
    _set(char, [key if p == replace else p for p in current], xp_map)
    return Outcome().add("prof.swapped", prof=name, old=c.professions[replace].name.model_dump(), cost=SWAP_COST)


def grant_xp(char: Character, key: str, amount: int, out: Outcome) -> None:
    if amount <= 0:
        return
    xp_map = dict((char.professions or {}).get("xp", {}))
    before = xp_map.get(key, 0)
    xp_map[key] = before + amount
    _set(char, active(char), xp_map)
    name = get_content().professions[key].name.model_dump()
    out.add("prof.xp", prof=name, amount=amount)
    after = gathering.rank_for(before + amount)
    if after > gathering.rank_for(before):
        out.add("prof.rank", prof=name, rank=after)
