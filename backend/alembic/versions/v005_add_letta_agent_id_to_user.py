"""add letta agent id to user"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "add_letta_agent_id_to_user"
down_revision = "create_persona_taxonomy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("letta_agent_id", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint("uq_user_letta_agent_id", "user", ["letta_agent_id"])


def downgrade() -> None:
    op.drop_constraint("uq_user_letta_agent_id", "user", type_="unique")
    op.drop_column("user", "letta_agent_id")
