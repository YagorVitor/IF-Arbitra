"""Keep administrative revisions separate from immutable automatic allocations."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011_admin_adjustments"
down_revision = "0010_trio_formation"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "allocation_adjustments",
        sa.Column("id", postgresql.UUID(), primary_key=True),
        sa.Column(
            "round_id", postgresql.UUID(), sa.ForeignKey("allocation_rounds.id"), nullable=False
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("assignments", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("executed_by", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("round_id", "revision"),
        sa.CheckConstraint("revision > 0"),
    )
    op.create_index("ix_allocation_adjustments_round_id", "allocation_adjustments", ["round_id"])
    op.execute("""
        CREATE TRIGGER adjustment_immutable BEFORE UPDATE OR DELETE ON allocation_adjustments
        FOR EACH ROW EXECUTE FUNCTION reject_change();
        CREATE TRIGGER adjustment_no_truncate BEFORE TRUNCATE ON allocation_adjustments
        FOR EACH STATEMENT EXECUTE FUNCTION reject_change();
    """)


def downgrade():
    op.drop_table("allocation_adjustments")
