"""characters.checks_tried (a skill check can't be retried in the same place until the next game day)

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-11 23:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

Json = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column('characters', sa.Column('checks_tried', Json, nullable=False, server_default='{}'))


def downgrade() -> None:
    op.drop_column('characters', 'checks_tried')
