"""characters.custom_background (a player-written background: name, story and the 2 skills chosen)

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-14 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

Json = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column('characters', sa.Column('custom_background', Json, nullable=True))


def downgrade() -> None:
    op.drop_column('characters', 'custom_background')
