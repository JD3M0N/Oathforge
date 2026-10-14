"""Console admin: list, find and delete single players (``oath delete-player``).

The cascade is done by hand from ``Base.metadata``: SQLite ignores ``ondelete`` without
``PRAGMA foreign_keys``, and some FKs (``crafted_by``, ``encounters.party_id``) have none.
"""

from dataclasses import dataclass

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.database.models import Base, Character, User


@dataclass
class Player:
    user_id: int
    telegram_id: int
    name: str | None  # None: no character yet
    class_key: str | None
    level: int | None


def _query():
    return (select(User.id, User.telegram_id, Character.name, Character.class_key, Character.level)
            .outerjoin(Character, Character.user_id == User.id).order_by(User.id))


async def list_players(session: AsyncSession) -> list[Player]:
    return [Player(*row) for row in await session.execute(_query())]


async def find_players(session: AsyncSession, query: str) -> list[Player]:
    """By Telegram id when ``query`` is a number, otherwise by character name (any case)."""
    query = query.strip()
    if query.lstrip("-").isdigit():
        where = User.telegram_id == int(query)
    else:
        where = func.lower(Character.name) == query.lower()
    return [Player(*row) for row in await session.execute(_query().where(where))]


async def delete_player(session: AsyncSession, user_id: int) -> dict[str, int]:
    """Delete a user and every row that hangs from them; returns rows deleted per table.

    FKs with ``ondelete="CASCADE"`` delete the child rows; any other FK is set to NULL, so
    other players keep the items this one crafted and their own combats.
    """
    doomed: dict[str, set] = {"users": {user_id}}
    tables = Base.metadata.sorted_tables  # parents before children
    for table in tables:
        for fk in table.foreign_keys:
            ids = doomed.get(fk.column.table.name)
            if ids and fk.ondelete == "CASCADE":
                (pk,) = table.primary_key.columns
                rows = await session.scalars(select(pk).where(fk.parent.in_(ids)))
                doomed.setdefault(table.name, set()).update(rows)
    for table in tables:
        for fk in table.foreign_keys:
            ids = doomed.get(fk.column.table.name)
            if ids and fk.ondelete != "CASCADE":
                await session.execute(update(table).where(fk.parent.in_(ids)).values({fk.parent.name: None}))
    counts = {}
    for table in reversed(tables):  # children first
        if ids := doomed.get(table.name):
            (pk,) = table.primary_key.columns
            await session.execute(delete(table).where(pk.in_(ids)))
            counts[table.name] = len(ids)
    return counts
