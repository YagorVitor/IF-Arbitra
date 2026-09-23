"""Add pending student accounts and one-time email verification state."""

import sqlalchemy as sa
from alembic import op

revision = "0005_email_verification"
down_revision = "0004_run_history"
branch_labels = depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email", sa.String(254), nullable=True))
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True)))
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_table(
        "email_verifications",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("code_hash", sa.String(64)),
        sa.Column("code_expires_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True)),
        sa.Column("setup_token_hash", sa.String(64)),
        sa.Column("setup_expires_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM users WHERE password_hash IS NULL"))
        .scalar()
    ):
        raise RuntimeError("Complete or remove pending accounts before downgrade")
    op.drop_table("email_verifications")
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
