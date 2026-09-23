"""persist AI analysis report

Revision ID: 0003_ai_report_persistence
Revises: 0002_analysis_history
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_ai_report_persistence"
down_revision: str | None = "0002_analysis_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("analysis", sa.Column("ai_report_json", sa.Text(), nullable=True))
    op.add_column("analysis", sa.Column("ai_model", sa.String(length=160), nullable=True))
    op.add_column(
        "analysis",
        sa.Column("ai_generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("analysis", "ai_generated_at")
    op.drop_column("analysis", "ai_model")
    op.drop_column("analysis", "ai_report_json")
