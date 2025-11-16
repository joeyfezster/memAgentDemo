"""create persona taxonomy"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

from app.db.persona_loader import load_persona_definitions

revision = "create_persona_taxonomy"
down_revision = "change_message_role_to_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "persona",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("handle", sa.String(length=255), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("professional_role", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("typical_kpis", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "typical_motivations", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
        ),
        sa.Column(
            "quintessential_queries", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
        ),
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
    op.create_table(
        "userpersona",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("persona_id", sa.String(length=36), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
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
        sa.UniqueConstraint("user_id", "persona_id", name="uq_user_persona"),
    )
    op.create_index("ix_userpersona_user_id", "userpersona", ["user_id"])
    op.create_index("ix_userpersona_persona_id", "userpersona", ["persona_id"])

    _seed_personas()


def downgrade() -> None:
    op.drop_index("ix_userpersona_persona_id", table_name="userpersona")
    op.drop_index("ix_userpersona_user_id", table_name="userpersona")
    op.drop_table("userpersona")
    op.drop_table("persona")


def _seed_personas() -> None:
    definitions = load_persona_definitions()
    if not definitions:
        return

    persona_table = sa.table(
        "persona",
        sa.column("id", sa.String(length=36)),
        sa.column("handle", sa.String(length=255)),
        sa.column("name", sa.String(length=255)),
        sa.column("industry", sa.String(length=255)),
        sa.column("professional_role", sa.String(length=255)),
        sa.column("description", sa.Text()),
        sa.column("typical_kpis", sa.JSON()),
        sa.column("typical_motivations", sa.JSON()),
        sa.column("quintessential_queries", sa.JSON()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    now = datetime.now(UTC)
    rows = [
        {
            "id": str(uuid4()),
            "handle": definition.persona_handle,
            "name": definition.display_name,
            "industry": definition.industry,
            "professional_role": definition.professional_role,
            "description": definition.description,
            "typical_kpis": definition.typical_kpis,
            "typical_motivations": definition.typical_motivations,
            "quintessential_queries": definition.quintessential_queries,
            "created_at": now,
            "updated_at": now,
        }
        for definition in definitions
    ]
    op.bulk_insert(persona_table, rows)
