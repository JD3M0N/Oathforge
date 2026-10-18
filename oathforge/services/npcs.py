"""NPC memory, relationships, faction reputation, rumors and theft."""

import random
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.content import get_content
from oathforge.database.models import Character, FactionReputation, NpcMemory, NpcRelationship, WorldFact
from oathforge.engine.checks import check
from oathforge.engine.dice import roll
from oathforge.services import characters
from oathforge.services import achievements
from oathforge.services.events import Outcome

MEMORY_LIMIT = 5
TRUST_RANGE = (-10, 10)
REP_RANGE = (-100, 100)


def _clamp(v: int, lo_hi: tuple[int, int]) -> int:
    return max(lo_hi[0], min(lo_hi[1], v))


# ---------------------------------------------------------------- memory

async def remember(session: AsyncSession, npc_key: str, char: Character, text: str, importance: int,
                   kind: str = "episodic") -> None:
    session.add(NpcMemory(npc_key=npc_key, character_id=char.id, kind=kind, text=text[:500],
                          importance=max(1, min(5, importance))))


async def recall(session: AsyncSession, npc_key: str, char: Character, limit: int = MEMORY_LIMIT) -> list[NpcMemory]:
    """Most important first, newest breaking ties. Only this NPC's memories of this character."""
    rows = await session.scalars(
        select(NpcMemory)
        .where(NpcMemory.npc_key == npc_key, NpcMemory.character_id == char.id)
        .order_by(NpcMemory.importance.desc(), NpcMemory.created_at.desc(), NpcMemory.id.desc())
        .limit(limit)
    )
    return list(rows)


async def relationship(session: AsyncSession, npc_key: str, char: Character, lock: bool = False) -> NpcRelationship:
    stmt = select(NpcRelationship).where(NpcRelationship.npc_key == npc_key, NpcRelationship.character_id == char.id)
    if lock:
        stmt = stmt.with_for_update()
    rel = await session.scalar(stmt)
    if rel is None:
        rel = NpcRelationship(npc_key=npc_key, character_id=char.id, trust=0, fear=0, debt=0)
        session.add(rel)
        await session.flush()
    return rel


async def adjust_trust(session: AsyncSession, npc_key: str, char: Character, delta: int) -> int:
    rel = await relationship(session, npc_key, char, lock=True)
    rel.trust = _clamp(rel.trust + delta, TRUST_RANGE)
    return rel.trust


# ---------------------------------------------------------------- reputation

async def reputations(session: AsyncSession, char: Character) -> dict[str, int]:
    rows = await session.scalars(select(FactionReputation).where(FactionReputation.character_id == char.id))
    return {r.faction_key: r.value for r in rows}


async def reputation_with(session: AsyncSession, char: Character, faction: str | None) -> int:
    if faction is None:
        return 0
    return (await reputations(session, char)).get(faction, 0)


async def adjust_reputation(session: AsyncSession, char: Character, faction: str, delta: int, out: Outcome) -> None:
    row = await session.scalar(
        select(FactionReputation)
        .where(FactionReputation.character_id == char.id, FactionReputation.faction_key == faction)
        .with_for_update()
    )
    if row is None:
        row = FactionReputation(character_id=char.id, faction_key=faction, value=0)
        session.add(row)
    row.value = _clamp(row.value + delta, REP_RANGE)
    out.add("rep.changed", faction=get_content().factions[faction].name.model_dump(),
            delta=f"{delta:+d}", value=row.value)
    await achievements.emit(session, char, out, "reputation", {"faction": faction, "value": row.value})


# ---------------------------------------------------------------- rumors

async def add_rumor(session: AsyncSession, text: dict, source: str, tags: list[str]) -> None:
    session.add(WorldFact(key=f"rumor:{uuid.uuid4().hex[:12]}", value={"text": text},
                          tags=["rumor", *tags], source=source))


async def recent_rumors(session: AsyncSession, limit: int = 3, exclude_character: int | None = None) -> list[dict]:
    rows = await session.scalars(select(WorldFact).where(WorldFact.key.like("rumor:%"))
                                 .order_by(WorldFact.created_at.desc(), WorldFact.id.desc()).limit(limit * 3))
    out = []
    for r in rows:
        if exclude_character is not None and f"character:{exclude_character}" in (r.tags or []):
            continue
        out.append(r.value["text"])
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------- theft

async def steal(session: AsyncSession, char: Character, npc_key: str, rng: random.Random) -> Outcome:
    """Sleight of Hand vs the NPC's passive perception.

    A clean success (margin >= 5) leaves no trace. A narrow success gets the
    gold but leaves the NPC suspicious. Failure is caught red-handed. The NPC
    remembers only what it could plausibly know.
    """
    npc = get_content().npcs[npc_key]
    if not npc.steal_gold:
        return Outcome.refused("steal.err.nothing")
    skills = await characters.skills_of(session, char)
    bonus = characters.skill_bonus(char, skills, "sleight_of_hand")
    dc = npc.passive_perception
    res = check(rng, "sleight_of_hand", bonus, dc)
    out = Outcome().add("check.result", skill=get_content().skills["sleight_of_hand"].name.model_dump(),
                        roll=res.kept, total=res.total, dc=dc,
                        result="✅" if res.success else "❌")
    name = npc.name.model_dump()
    if res.success:
        gold = roll(npc.steal_gold, rng).total
        char.gold += gold
        out.add("steal.success", npc=name, gold=gold)
        if res.margin < 5:
            await remember(session, npc_key, char,
                           f"Coins went missing from my purse right after {char.name} stood next to me. I suspect them.", 4)
            await adjust_trust(session, npc_key, char, -1)
            out.add("steal.suspected", npc=name)
        await characters.practice(session, char, "sleight_of_hand", "medium", f"steal:{npc_key}", out)
    else:
        await remember(session, npc_key, char, f"I caught {char.name} trying to pick my pocket.", 5)
        await adjust_trust(session, npc_key, char, -3)
        out.add("steal.caught", npc=name)
        if npc.faction:
            await adjust_reputation(session, char, npc.faction, -10, out)
    return out
