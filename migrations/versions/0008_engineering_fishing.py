"""Artificing becomes Engineering, and Fishing a hobby like Cooking (v0.7.20)

characters.professions: the key "artificing" -> "engineering" (active list and xp);
characters.masteries["fishing"] -> characters.professions["xp"]["fishing"].

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-15 12:00:00.000000
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

characters = sa.table("characters", sa.column("id", sa.Integer), sa.column("professions", sa.JSON),
                      sa.column("masteries", sa.JSON))


def _load(value):
    if value is None:
        return {}
    return json.loads(value) if isinstance(value, str) else dict(value)


def _migrate(forward: bool) -> None:
    conn = op.get_bind()
    old, new = ("artificing", "engineering") if forward else ("engineering", "artificing")
    for row in conn.execute(sa.select(characters.c.id, characters.c.professions, characters.c.masteries)).all():
        profs, masteries = _load(row.professions), _load(row.masteries)
        active = [new if k == old else k for k in profs.get("active", [])]
        xp = {(new if k == old else k): v for k, v in profs.get("xp", {}).items()}
        if forward and "fishing" in masteries:
            xp["fishing"] = int(xp.get("fishing", 0)) + int(masteries.pop("fishing"))
        elif not forward and "fishing" in xp:
            masteries["fishing"] = int(xp.pop("fishing"))
        new_profs = {"active": active, "xp": xp} if profs or xp else profs
        if new_profs != _load(row.professions) or masteries != _load(row.masteries):
            conn.execute(characters.update().where(characters.c.id == row.id)
                         .values(professions=new_profs, masteries=masteries))


def upgrade() -> None:
    _migrate(forward=True)


def downgrade() -> None:
    _migrate(forward=False)
