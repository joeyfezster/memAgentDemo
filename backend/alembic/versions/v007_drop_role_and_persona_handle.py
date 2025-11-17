"""drop role and persona_handle from user

Revision ID: drop_role_and_persona_handle
Revises: seed_personas
Create Date: 2025-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "drop_role_and_persona_handle"
down_revision: Union[str, None] = "seed_personas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("user", "persona_handle")
    op.drop_column("user", "role")


def downgrade() -> None:
    op.add_column("user", sa.Column("role", sa.String(length=255), nullable=True))
    op.add_column(
        "user", sa.Column("persona_handle", sa.String(length=255), nullable=False)
    )
