"""characters.gender: male | female (chooses the class portrait); NULL for older characters

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-11 19:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('characters', sa.Column('gender', sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column('characters', 'gender')
