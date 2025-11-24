"""add message metadata

Revision ID: add_message_metadata
Revises: create_conversations_and_messages
Create Date: 2025-11-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "add_message_metadata"
down_revision: Union[str, None] = "create_conversations_and_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("message", sa.Column("metadata", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("message", "metadata")
