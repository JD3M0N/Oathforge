"""The launch reset and its safety net (roadmap_balance §16): wipe the game, keep the people.

``reset_for_launch`` deletes every character and everything the game wrote around them (items, quests, achievements,
reputation, rumours, encounters, pending activities...) and keeps:

- the accounts (``users``) with their general preferences (language, manual rolls); anything pointing at a vanished
  character is dropped from ``settings``,
- the AI quota counters (``ai_usage``): resetting characters must never reset the daily budget,
- ``media_files`` (Telegram file ids cached for the art) and ``action_logs`` (the technical audit, with its links to
  characters and users cleared).

``dump`` / ``restore`` are a logical backup of the whole database in one JSON file: the rehearsal for the launch (take
it, reset on a copy, restore, compare the counts) and the way back if the reset fails before the doors open.
They work on SQLite and PostgreSQL; on PostgreSQL ``pg_dump`` stays the production backup, this is the portable one.
"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import delete, func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.database.models import ActionLog, Base, User

KEEP_TABLES = ("users", "ai_usage", "media_files", "action_logs")
KEEP_SETTINGS = ("manual_rolls",)  # the general preferences; "keyboard" and the like are tied to the old game


@dataclass
class Report:
    before: dict[str, int]
    after: dict[str, int] = field(default_factory=dict)
    applied: bool = False
    orphans: list[str] = field(default_factory=list)  # references to rows that no longer exist, after the reset
    settings_trimmed: int = 0

    @property
    def wiped(self) -> dict[str, int]:
        return {t: n for t, n in self.before.items() if t not in KEEP_TABLES and n}

    @property
    def kept(self) -> dict[str, int]:
        return {t: self.before[t] for t in KEEP_TABLES if t in self.before}


async def counts(session: AsyncSession) -> dict[str, int]:
    return {t.name: await session.scalar(select(func.count()).select_from(t)) or 0 for t in Base.metadata.sorted_tables}


async def orphans(session: AsyncSession) -> list[str]:
    """Foreign keys that point at a row that is gone: the check that nothing was left hanging."""
    found = []
    for table in Base.metadata.sorted_tables:
        for fk in table.foreign_keys:
            parent = fk.column.table
            stmt = (
                select(func.count())
                .select_from(table)
                .where(fk.parent.is_not(None), fk.parent.not_in(select(fk.column)))
            )
            n = await session.scalar(stmt)
            if n:
                found.append(f"{table.name}.{fk.parent.name} -> {parent.name}: {n}")
    return found


async def reset_for_launch(session: AsyncSession, apply: bool = False) -> Report:
    """Count what would go (``apply=False``) or do it. The caller commits; nothing is committed here."""
    report = Report(before=await counts(session))
    if not apply:
        return report
    tables = [t for t in Base.metadata.sorted_tables if t.name not in KEEP_TABLES]
    await session.execute(update(ActionLog).values(character_id=None))  # the audit stays, its links do not
    for table in reversed(tables):  # children first
        await session.execute(delete(table))
    for user in (await session.scalars(select(User))).all():
        kept = {k: v for k, v in (user.settings or {}).items() if k in KEEP_SETTINGS}
        if kept != (user.settings or {}):
            report.settings_trimmed += 1
            user.settings = kept
    await session.flush()
    report.after = await counts(session)
    report.orphans = await orphans(session)
    report.applied = True
    return report


# ---------------------------------------------------------------- logical backup


def _plain(value):
    if isinstance(value, datetime):
        return {"$dt": value.isoformat()}
    if isinstance(value, date):
        return {"$d": value.isoformat()}
    return value


def _back(column, value):
    if isinstance(value, dict) and set(value) == {"$dt"}:
        return datetime.fromisoformat(value["$dt"])
    if isinstance(value, dict) and set(value) == {"$d"}:
        return date.fromisoformat(value["$d"])
    return value


async def dump(session: AsyncSession) -> dict:
    """Every row of every table, JSON-safe, with the version of the schema it came from."""
    data: dict = {"format": 1, "tables": {}}
    for table in Base.metadata.sorted_tables:
        rows = (await session.execute(select(table))).mappings().all()
        data["tables"][table.name] = [{k: _plain(v) for k, v in row.items()} for row in rows]
    return data


async def restore(session: AsyncSession, data: dict) -> dict[str, int]:
    """Replace the whole database with a dump: delete everything, insert in parent-first order, fix the sequences."""
    if data.get("format") != 1:
        raise ValueError("not an Oathforge backup")
    tables = Base.metadata.sorted_tables
    unknown = set(data["tables"]) - {t.name for t in tables}
    if unknown:
        raise ValueError(f"the backup has tables this version does not know: {sorted(unknown)}")
    for table in reversed(tables):
        await session.execute(delete(table))
    out = {}
    for table in tables:
        rows = data["tables"].get(table.name, [])
        known = {c.name: c for c in table.columns}
        clean = [{k: _back(known[k], v) for k, v in row.items() if k in known} for row in rows]
        if clean:
            await session.execute(insert(table), clean)
        out[table.name] = len(clean)
    if (
        session.bind is not None and session.bind.dialect.name == "postgresql"
    ):  # inserted ids must not collide with the next ones
        for table in tables:
            pk = list(table.primary_key.columns)
            if len(pk) == 1 and pk[0].autoincrement is not False and pk[0].type.python_type is int:
                await session.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('\"{table.name}\"', '{pk[0].name}'), "
                        f'COALESCE((SELECT MAX("{pk[0].name}") FROM "{table.name}"), 1), '
                        f'(SELECT MAX("{pk[0].name}") FROM "{table.name}") IS NOT NULL)'
                    )
                )
    return out


def to_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)
