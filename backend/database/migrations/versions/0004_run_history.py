"""Protect completed execution evidence from later changes."""

from alembic import op

revision = "0004_run_history"
down_revision = "0003_audit_context"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE FUNCTION protect_run_history() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF TG_OP = 'DELETE' OR OLD.status IN ('COMPLETED', 'FAILED') THEN
        RAISE EXCEPTION 'Finished execution evidence is immutable' USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER run_history_guard BEFORE UPDATE OR DELETE ON allocation_runs
      FOR EACH ROW EXECUTE FUNCTION protect_run_history();
    CREATE TRIGGER run_no_truncate BEFORE TRUNCATE ON allocation_runs
      FOR EACH STATEMENT EXECUTE FUNCTION reject_change();
    """)


def downgrade():
    op.execute("DROP TRIGGER run_no_truncate ON allocation_runs")
    op.execute("DROP TRIGGER run_history_guard ON allocation_runs")
    op.execute("DROP FUNCTION protect_run_history()")
