"""add_user_memory_document"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "v004"
down_revision = "v003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("memory_document", JSONB, nullable=False, server_default="{}"),
    )

    op.create_index(
        "ix_user_memory_document",
        "user",
        ["memory_document"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_user_memory_document", table_name="user")
    op.drop_column("user", "memory_document")
