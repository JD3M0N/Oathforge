"""What a character knows about crafting: learned special recipes, branches and chosen tools (v0.10.13)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None
Json = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    op.add_column("characters", sa.Column("crafting", Json, nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("characters", "crafting")
