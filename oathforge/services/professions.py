"""Crafting professions: two active, learned and swapped with the master of that trade, at their stall.

Swapping keeps the XP of the profession you drop, so trying another one never wastes progress.
Hobbies (cooking, fishing) take no slot: everyone can practise them. Fishing has no station: it levels by fishing.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.database.models import Character
from oathforge.engine import gathering
from oathforge.services import characters, quests
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
    if key not in c.professions:
        return Outcome.refused("prof.err.unknown")
    if c.professions[key].hobby:
        return Outcome.refused("prof.err.hobby", prof=c.professions[key].name.model_dump())
    here = c.locations[char.location].teaches
    if here is None:
        return Outcome.refused("prof.err.not_guild")
    if here != key:
        return Outcome.refused(
            "prof.err.elsewhere", prof=c.professions[key].name.model_dump(), place=_stall_phrase(key)
        )
    current = active(char)
    if key in current:
        return Outcome.refused("prof.err.already", prof=c.professions[key].name.model_dump())
    xp_map = dict((char.professions or {}).get("xp", {}))
    name = c.professions[key].name.model_dump()
    if len(current) < SLOTS:
        _set(char, current + [key], xp_map)
        out = Outcome().add("prof.learned", prof=name, used=len(current) + 1, slots=SLOTS)
        return out.extend(await quests.on_event(session, char, "learn_profession", key))
    if replace not in current:
        return Outcome.refused("prof.err.slots_full", slots=SLOTS)
    if char.gold < SWAP_COST:
        return Outcome.refused("shop.err.no_gold", price=SWAP_COST)
    char.gold -= SWAP_COST
    _set(char, [key if p == replace else p for p in current], xp_map)
    out = Outcome().add("prof.swapped", prof=name, old=c.professions[replace].name.model_dump(), cost=SWAP_COST)
    return out.extend(await quests.on_event(session, char, "learn_profession", key))


def stall_of(key: str) -> str | None:
    """The place whose master teaches this profession."""
    return next((k for k, loc in get_content().locations.items() if loc.teaches == key), None)


def _stall_phrase(key: str) -> dict:
    place = stall_of(key)
    return get_content().locations[place].phrase() if place else {"es": "?", "en": "?"}


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
        announce_techniques(key, gathering.rank_for(before), after, out)


def announce_techniques(key: str, before: int, after: int, out: Outcome) -> None:
    """Every technique the new rank unlocks, each with the recipes it brings, in one line."""
    c = get_content()
    prof = c.professions.get(key)
    if prof is None:
        return
    for tech_key, tech in prof.techniques.items():
        if not before < tech.rank <= after:
            continue
        made = [
            c.items[next(iter(r.outputs))].name
            for r in c.recipes.values()
            if r.technique == tech_key and r.profession == key
        ]
        out.add(
            "prof.technique",
            technique=tech.name.model_dump(),
            items={lang: ", ".join(m.get(lang) for m in made) for lang in ("es", "en")},
        )
