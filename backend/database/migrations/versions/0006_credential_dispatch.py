"""Retire self-service email challenges in favor of administrator dispatch."""

import sqlalchemy as sa
from alembic import op

revision = "0006_credential_dispatch"
down_revision = "0005_email_verification"
branch_labels = depends_on = None


def upgrade():
    op.alter_column("users", "login", existing_type=sa.String(160), type_=sa.String(254))
    op.drop_table("email_verifications")


def downgrade():
    if (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM users WHERE length(login) > 160"))
        .scalar()
    ):
        raise RuntimeError("Shorten long logins before downgrading")
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
    op.alter_column("users", "login", existing_type=sa.String(254), type_=sa.String(160))
