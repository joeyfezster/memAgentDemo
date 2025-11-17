"""create personas tables

Revision ID: create_personas
Revises: change_message_role_to_enum
Create Date: 2025-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "create_personas"
down_revision: Union[str, None] = "change_message_role_to_enum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "persona",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("professional_role", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("typical_kpis", sa.Text, nullable=False),
        sa.Column("typical_motivations", sa.Text, nullable=False),
        sa.Column("quintessential_queries", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_persona_name", "persona", ["name"], unique=True)

    op.create_table(
        "user_persona",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("persona_id", sa.String(length=36), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="1.0"),
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_confirmed",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["persona_id"], ["persona.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_persona_user_id", "user_persona", ["user_id"])
    op.create_index("ix_user_persona_persona_id", "user_persona", ["persona_id"])


def downgrade() -> None:
    op.drop_index("ix_user_persona_persona_id", table_name="user_persona")
    op.drop_index("ix_user_persona_user_id", table_name="user_persona")
    op.drop_table("user_persona")
    op.drop_index("ix_persona_name", table_name="persona")
    op.drop_table("persona")
