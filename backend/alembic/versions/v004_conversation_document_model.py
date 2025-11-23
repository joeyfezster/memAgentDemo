"""conversation_document_model"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "v004"
down_revision = "v002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.drop_table("message")

    op.add_column(
        "conversation",
        sa.Column("messages_document", JSONB, nullable=False, server_default="[]"),
    )

    op.execute(
        """
        ALTER TABLE conversation
        ADD COLUMN embedding vector(1536)
        """
    )

    op.create_index(
        "idx_messages_document_gin",
        "conversation",
        ["messages_document"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"messages_document": "jsonb_path_ops"},
    )

    op.execute(
        """
        CREATE INDEX idx_messages_content_gin ON conversation
        USING gin ((messages_document::text) gin_trgm_ops)
        """
    )


def downgrade() -> None:
    op.create_table(
        "message",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("conversation.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.drop_index("idx_messages_content_gin", table_name="conversation")
    op.drop_index("idx_messages_document_gin", table_name="conversation")

    op.execute("ALTER TABLE conversation DROP COLUMN embedding")
    op.drop_column("conversation", "messages_document")
