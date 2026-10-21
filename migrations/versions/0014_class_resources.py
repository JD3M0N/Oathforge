"""The class's own bar (Conviction, Focus, Mana…) instead of uses per rest (v0.10.25)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None
Json = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    # {"v": 1, "<resource>": how much is left}. Empty means a full bar: nobody loses what they never spent.
    op.add_column("characters", sa.Column("pools", Json, nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("characters", "pools")
