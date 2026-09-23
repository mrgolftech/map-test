"""analysis history persistence

Revision ID: 0002_analysis_history
Revises: 0001_foundation
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_analysis_history"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("product_id", sa.String(length=160), nullable=True),
        sa.Column("lot_id", sa.String(length=160), nullable=True),
        sa.Column("wafer_id", sa.String(length=160), nullable=True),
        sa.Column("flow_id", sa.String(length=160), nullable=True),
        sa.Column("yield", sa.Float(), nullable=True),
        sa.Column("tested_die", sa.Integer(), nullable=False),
        sa.Column("pass_die", sa.Integer(), nullable=False),
        sa.Column("fail_die", sa.Integer(), nullable=False),
        sa.Column("main_fail_bin", sa.Integer(), nullable=True),
        sa.Column("main_pattern", sa.String(length=80), nullable=True),
        sa.Column("validation_status", sa.String(length=16), nullable=False),
        sa.Column("dataset_json", sa.Text(), nullable=False),
        sa.Column("analysis_summary_json", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.Text(), nullable=False),
        sa.Column("validation_json", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_created_at", "analysis", ["created_at"])
    op.create_index("ix_analysis_product_id", "analysis", ["product_id"])
    op.create_index("ix_analysis_lot_id", "analysis", ["lot_id"])
    op.create_index("ix_analysis_wafer_id", "analysis", ["wafer_id"])
    op.create_index("ix_analysis_yield", "analysis", ["yield"])
    op.create_index("ix_analysis_main_fail_bin", "analysis", ["main_fail_bin"])
    op.create_index("ix_analysis_main_pattern", "analysis", ["main_pattern"])


def downgrade() -> None:
    op.drop_index("ix_analysis_main_pattern", table_name="analysis")
    op.drop_index("ix_analysis_main_fail_bin", table_name="analysis")
    op.drop_index("ix_analysis_yield", table_name="analysis")
    op.drop_index("ix_analysis_wafer_id", table_name="analysis")
    op.drop_index("ix_analysis_lot_id", table_name="analysis")
    op.drop_index("ix_analysis_product_id", table_name="analysis")
    op.drop_index("ix_analysis_created_at", table_name="analysis")
    op.drop_table("analysis")
