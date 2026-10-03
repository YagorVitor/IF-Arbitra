"""Administrative reservations for future group allocations."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014_staff_reservations"
down_revision = "0013_captain_access"
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        "staff_reservations",
        sa.Column("captain_id", postgresql.UUID(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column(
            "staff_id",
            postgresql.UUID(),
            sa.ForeignKey("institutional_staff.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("updated_by", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("staff_reservations")
