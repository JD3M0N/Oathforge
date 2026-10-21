"""The hero's progression choices in one versioned blob: milestones, trainings and modifiers (v0.10.22)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None
Json = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    # {"v": 1, "milestones": [...], "choices": {"training:5": "...", "modifier:13": "..."},
    #  "companion": {...}, "reroll": true}. The class branch stays in characters.specialization.
    op.add_column("characters", sa.Column("build", Json, nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("characters", "build")
