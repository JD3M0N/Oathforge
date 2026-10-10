"""Audit log and idempotency.

Every state-changing button carries a nonce. The first time a
(user, nonce) pair is claimed inside the action's transaction it is
recorded; a replay (double tap, Telegram retry, stale keyboard) finds the
unique key taken and is ignored.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from oathforge.database.models import ActionLog


async def claim(
    session: AsyncSession,
    key: str | None,
    *,
    user_id: int | None,
    character_id: int | None,
    verb: str,
    payload: dict | None = None,
) -> ActionLog | None:
    """Insert the audit row. Returns None if ``key`` was already used."""
    row = ActionLog(
        idempotency_key=key, user_id=user_id, character_id=character_id,
        verb=verb, payload=payload or {}, result={},
    )
    if key is not None:
        existing = await session.scalar(select(ActionLog.id).where(ActionLog.idempotency_key == key))
        if existing is not None:
            return None
    try:
        async with session.begin_nested():
            session.add(row)
    except IntegrityError:
        return None
    return row


async def log(session: AsyncSession, *, user_id, character_id, verb: str, payload=None, result=None) -> None:
    session.add(ActionLog(user_id=user_id, character_id=character_id, verb=verb,
                          payload=payload or {}, result=result or {}))
