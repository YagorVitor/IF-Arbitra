"""Add searchable entity context to audit events."""

import sqlalchemy as sa
from alembic import op

revision = "0003_audit_context"
down_revision = "0002_integrity"
branch_labels = depends_on = None


def upgrade():
    op.add_column("audit_events", sa.Column("entity_type", sa.String(length=40), nullable=True))
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])


def downgrade():
    op.drop_index("ix_audit_events_entity_type", table_name="audit_events")
    op.drop_column("audit_events", "entity_type")
