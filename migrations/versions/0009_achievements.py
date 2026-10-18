"""Achievement identity and encounter metrics (v0.9.0)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None
Json = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    op.add_column("encounters", sa.Column("achievement_metrics", Json, nullable=True))
    common = lambda: [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False),
    ]
    for name, extra, unique in [
        ("achievement_progress", [sa.Column("achievement_key", sa.String(32), nullable=False),
         sa.Column("edition", sa.String(16), nullable=False), sa.Column("state", Json, nullable=False)],
         ("character_id", "achievement_key", "edition")),
        ("achievement_unlocks", [sa.Column("achievement_key", sa.String(32), nullable=False),
         sa.Column("edition", sa.String(16), nullable=False), sa.Column("points", sa.Integer(), nullable=False),
         sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False), sa.Column("evidence", Json, nullable=False),
         sa.Column("retroactive", sa.Boolean(), nullable=False)], ("character_id", "achievement_key", "edition")),
        ("achievement_event_receipts", [sa.Column("event_id", sa.String(160), nullable=False),
         sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)], ("character_id", "event_id")),
        ("achievement_notifications", [sa.Column("unlocks", Json, nullable=False),
         sa.Column("status", sa.String(16), nullable=False), sa.Column("lease_until", sa.Float(), nullable=False),
         sa.Column("token", sa.String(32)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)], ()),
    ]:
        constraints = [sa.UniqueConstraint(*unique)] if unique else []
        op.create_table(name, *common(), *extra, *constraints)
        op.create_index(f"ix_{name}_character_id", name, ["character_id"])
    op.create_index("ix_achievement_notifications_status", "achievement_notifications", ["status"])
    op.create_table("achievement_preferences",
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("title", sa.String(32)), sa.Column("featured", Json, nullable=False),
        sa.Column("tracked", Json, nullable=False), sa.Column("revealed", Json, nullable=False))


def downgrade():
    for name in ("achievement_preferences", "achievement_notifications", "achievement_event_receipts",
                 "achievement_unlocks", "achievement_progress"):
        op.drop_table(name)
    op.drop_column("encounters", "achievement_metrics")
