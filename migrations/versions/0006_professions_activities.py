"""world_activities (timed field activities) and characters.masteries / professions / cooldowns

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-13 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

Json = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
OPEN_ACTIVITY = "status IN ('running', 'awaiting_combat')"


def upgrade() -> None:
    op.add_column('characters', sa.Column('masteries', Json, nullable=False, server_default='{}'))
    op.add_column('characters', sa.Column('professions', Json, nullable=False, server_default='{}'))
    op.add_column('characters', sa.Column('cooldowns', Json, nullable=False, server_default='{}'))
    op.create_table(
        'world_activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('character_id', sa.Integer(), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location', sa.String(64), nullable=False),
        sa.Column('kind', sa.String(16), nullable=False),
        sa.Column('skill', sa.String(32), nullable=False),
        sa.Column('started_at', sa.Float(), nullable=False),
        sa.Column('ends_at', sa.Float(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('seed', sa.BigInteger(), nullable=False),
        sa.Column('result', Json, nullable=False),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chronicle', sa.Text(), nullable=True),
        sa.Column('chronicle_ai', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('resolved_at', sa.Float(), nullable=True),
    )
    op.create_index('ix_world_activities_character_id', 'world_activities', ['character_id'])
    op.create_index('ix_world_activities_resolved_at', 'world_activities', ['resolved_at'])
    op.create_index('uq_open_activity_per_character', 'world_activities', ['character_id'], unique=True,
                    postgresql_where=sa.text(OPEN_ACTIVITY), sqlite_where=sa.text(OPEN_ACTIVITY))


def downgrade() -> None:
    op.drop_index('uq_open_activity_per_character', table_name='world_activities')
    op.drop_index('ix_world_activities_resolved_at', table_name='world_activities')
    op.drop_index('ix_world_activities_character_id', table_name='world_activities')
    op.drop_table('world_activities')
    op.drop_column('characters', 'cooldowns')
    op.drop_column('characters', 'professions')
    op.drop_column('characters', 'masteries')
