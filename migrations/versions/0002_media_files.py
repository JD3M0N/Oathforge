"""media_files: cache of Telegram file_ids per bot

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-11 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('media_files',
    sa.Column('bot_id', sa.BigInteger(), nullable=False),
    sa.Column('asset_key', sa.String(length=255), nullable=False),
    sa.Column('checksum', sa.String(length=64), nullable=False),
    sa.Column('file_id', sa.String(length=255), nullable=False),
    sa.Column('file_unique_id', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('bot_id', 'asset_key')
    )


def downgrade() -> None:
    op.drop_table('media_files')
