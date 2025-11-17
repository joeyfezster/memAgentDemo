"""add letta_agent_id to user

Revision ID: add_letta_agent_id
Revises: create_personas
Create Date: 2025-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "add_letta_agent_id"
down_revision: Union[str, None] = "create_personas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user", sa.Column("letta_agent_id", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("user", "letta_agent_id")
