"""Store roster emails and preserve soft-removed students."""

import sqlalchemy as sa
from alembic import op

revision = "0007_initial_roster"
down_revision = "0006_credential_dispatch"
branch_labels = depends_on = None


def upgrade():
    op.add_column("users", sa.Column("removed_at", sa.DateTime(timezone=True)))
    op.add_column("institutional_staff", sa.Column("email", sa.String(254)))
    op.create_unique_constraint("uq_institutional_staff_email", "institutional_staff", ["email"])
    # The current roster replaces Junior with Marcel. Existing rounds keep their frozen staff.
    op.execute(
        sa.text(
            """
            UPDATE institutional_staff AS staff
            SET active = false, updated_at = now()
            WHERE staff.id = 'b3601f91-e41f-46d8-bc43-000000000006'
              AND staff.name = 'Junior Fernandes Marques'
            """
        )
    )


def downgrade():
    op.drop_constraint("uq_institutional_staff_email", "institutional_staff", type_="unique")
    op.drop_column("institutional_staff", "email")
    op.drop_column("users", "removed_at")
