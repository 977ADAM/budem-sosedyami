"""Create anonymous browser sessions.

Revision ID: 0001_anonymous_chat_sessions
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_anonymous_chat_sessions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anonymous_chat_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("token_hash", sa.CHAR(length=64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cleanup_pending", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "anonymous_chat_sessions_expires_at_idx",
        "anonymous_chat_sessions",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("anonymous_chat_sessions_expires_at_idx", table_name="anonymous_chat_sessions")
    op.drop_table("anonymous_chat_sessions")
