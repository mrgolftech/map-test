"""Persist encrypted LLM configuration.

Revision ID: 0004_llm_runtime_config
Revises: 0003_ai_report_persistence
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_llm_runtime_config"
down_revision = "0003_ai_report_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_runtime_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("base_url", sa.String(length=512), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("llm_runtime_config")
