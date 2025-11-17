"""change_message_role_to_enum"""

from alembic import op

revision = "v003"
down_revision = "v002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE message SET role = '_agent' WHERE role = 'assistant'")


def downgrade() -> None:
    op.execute("UPDATE message SET role = 'assistant' WHERE role = '_agent'")
