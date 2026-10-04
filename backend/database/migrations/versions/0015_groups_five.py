"""Allow five-member groups without changing existing groups or responses."""

import sqlalchemy as sa
from alembic import op

revision = "0015_groups_five"
down_revision = "0014_staff_reservations"
branch_labels = depends_on = None


def replace_size_rule(before, after):
    definition = op.get_bind().scalar(
        sa.text("SELECT pg_get_functiondef('validate_composition()'::regprocedure)")
    )
    if before not in definition:
        raise RuntimeError("Unexpected group composition validation function")
    op.execute(definition.replace(before, after))


def upgrade():
    replace_size_rule("n NOT IN (6, 7)", "n NOT IN (5, 6, 7)")


def downgrade():
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM sextets s JOIN allocation_rounds r "
            "ON r.id = s.round_id WHERE r.formation_mode = 'GROUPS' AND s.member_count = 5)"
        )
    ):
        raise RuntimeError("Cannot downgrade while five-member groups exist")
    replace_size_rule("n NOT IN (5, 6, 7)", "n NOT IN (6, 7)")
