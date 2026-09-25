"""Persist analysis and comparison AI conversations."""

import sqlalchemy as sa
from alembic import op

revision = "0005_ai_conversations"
down_revision = "0004_llm_runtime_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_conversation_thread",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scope", sa.String(length=24), nullable=False),
        sa.Column("context_key", sa.String(length=128), nullable=False),
        sa.Column("context_ids_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scope", "context_key", name="uq_ai_thread_scope_context"
        ),
    )
    op.create_index(
        "ix_ai_thread_updated_at", "ai_conversation_thread", ["updated_at"]
    )
    op.create_table(
        "ai_conversation_message",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("thread_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.Text(), nullable=False),
        sa.Column("limitations_json", sa.Text(), nullable=False),
        sa.Column("insufficient_evidence", sa.Boolean(), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["thread_id"], ["ai_conversation_thread.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_message_thread_created",
        "ai_conversation_message",
        ["thread_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_message_thread_created", table_name="ai_conversation_message")
    op.drop_table("ai_conversation_message")
    op.drop_index("ix_ai_thread_updated_at", table_name="ai_conversation_thread")
    op.drop_table("ai_conversation_thread")
