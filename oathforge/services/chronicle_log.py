"""Reads the chronicle of hero facts. Never writes: the facts come from achievements.emit."""

from sqlalchemy import func, select

from oathforge.database.models import HeroFact

PAGE_SIZE = 8


async def page(session, character, number: int = 0) -> tuple[list[HeroFact], bool, int]:
    """One page of entries, newest first; whether another page follows; and the hero's first day,
    so the book counts days from «Día 1» instead of the world's absolute day."""
    number = max(0, number)
    rows = (
        await session.scalars(
            select(HeroFact)
            .where(HeroFact.character_id == character.id, HeroFact.notable.is_(True))
            .order_by(HeroFact.id.desc())
            .offset(number * PAGE_SIZE)
            .limit(PAGE_SIZE + 1)
        )
    ).all()
    first = (
        await session.scalar(
            select(func.min(HeroFact.game_day)).where(HeroFact.character_id == character.id, HeroFact.game_day > 0)
        )
        or 0
    )
    return list(rows[:PAGE_SIZE]), len(rows) > PAGE_SIZE, first


async def counts(session, character) -> dict:
    """Verifiable totals: every number is the count of facts the engine recorded."""
    by_kind = dict(
        (
            await session.execute(
                select(HeroFact.kind, func.count()).where(HeroFact.character_id == character.id).group_by(HeroFact.kind)
            )
        ).all()
    )
    distinct = dict(
        (
            await session.execute(
                select(HeroFact.kind, func.count(func.distinct(HeroFact.tag)))
                .where(HeroFact.character_id == character.id, HeroFact.tag.is_not(None))
                .group_by(HeroFact.kind)
            )
        ).all()
    )
    return {
        "crafts": by_kind.get("craft", 0),
        "recipes": distinct.get("craft", 0),
        "discoveries": by_kind.get("discovery", 0),
        "quests": by_kind.get("quest", 0),
        "levels": by_kind.get("level", 0),
        "monsters_known": distinct.get("seen", 0),
        "species_killed": distinct.get("kill", 0),
    }
