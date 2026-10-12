"""quest_progress.counters (mission objectives) and characters.bestiary (monsters seen and killed)

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-11 23:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

Json = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column('characters', sa.Column('bestiary', Json, nullable=False, server_default='{}'))
    op.add_column('quest_progress', sa.Column('counters', Json, nullable=False, server_default='{}'))


def downgrade() -> None:
    op.drop_column('quest_progress', 'counters')
    op.drop_column('characters', 'bestiary')
