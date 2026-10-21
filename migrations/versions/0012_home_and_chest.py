"""Your room at the guild: the bed you rest in and the chest your items sit in (v0.10.14)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None
Json = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    # null: the backpack, as until now; "chest": stored in the room's chest
    op.add_column("item_instances", sa.Column("container", sa.String(16), nullable=True))
    op.create_index("ix_item_instances_container", "item_instances", ["owner_character_id", "container"])
    op.add_column("characters", sa.Column("home", Json, nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("characters", "home")
    op.drop_index("ix_item_instances_container", table_name="item_instances")
    op.drop_column("item_instances", "container")
