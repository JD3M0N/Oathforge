"""The chronicle of facts replaces the achievement receipts (v0.10.7)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None
Json = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    op.create_table("hero_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.String(160), nullable=False),
        sa.Column("kind", sa.String(24), nullable=False),
        sa.Column("data", Json, nullable=False),
        sa.Column("tag", sa.String(64)),
        sa.Column("game_day", sa.Integer(), nullable=False),
        sa.Column("notable", sa.Boolean(), nullable=False),
        sa.Column("retroactive", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("character_id", "event_id"))
    op.create_index("ix_hero_facts_character_id", "hero_facts", ["character_id"])
    op.create_index("ix_hero_facts_chronicle", "hero_facts", ["character_id", "notable", "id"])
    op.create_index("ix_hero_facts_tag", "hero_facts", ["character_id", "tag"])
    # The old receipts keep deduplicating grants; they have no kind or data, so they stay out of the chronicle.
    op.execute("INSERT INTO hero_facts (character_id, event_id, kind, data, game_day, notable, retroactive, created_at) "
               "SELECT character_id, event_id, 'legacy', '{}', 0, false, true, created_at "
               "FROM achievement_event_receipts")
    op.drop_table("achievement_event_receipts")


def downgrade():
    op.create_table("achievement_event_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("character_id", "event_id"))
    op.create_index("ix_achievement_event_receipts_character_id", "achievement_event_receipts", ["character_id"])
    op.execute("INSERT INTO achievement_event_receipts (character_id, event_id, created_at) "
               "SELECT character_id, event_id, created_at FROM hero_facts")
    op.drop_table("hero_facts")