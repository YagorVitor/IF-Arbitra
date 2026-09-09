"""Deferred composition/ranking checks, immutable priority, append-only audit."""

from alembic import op

revision = "0002_integrity"
down_revision = "0001_schema"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE FUNCTION reject_change() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'This record is immutable' USING ERRCODE = '23514'; END $$;
    CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_events
      FOR EACH ROW EXECUTE FUNCTION reject_change();
    CREATE TRIGGER audit_no_truncate BEFORE TRUNCATE ON audit_events
      FOR EACH STATEMENT EXECUTE FUNCTION reject_change();
    CREATE TRIGGER sextet_immutable BEFORE UPDATE OR DELETE ON sextets
      FOR EACH ROW EXECUTE FUNCTION reject_change();
    CREATE TRIGGER allocation_immutable BEFORE UPDATE OR DELETE ON allocations
      FOR EACH ROW EXECUTE FUNCTION reject_change();

    CREATE FUNCTION validate_composition() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; n integer; leader uuid; creator uuid;
    BEGIN
      IF TG_TABLE_NAME = 'sextets' THEN sid := NEW.id; ELSE sid := COALESCE(NEW.sextet_id, OLD.sextet_id); END IF;
      SELECT created_by INTO creator FROM sextets WHERE id = sid;
      IF creator IS NULL THEN RETURN NULL; END IF;
      SELECT count(*) INTO n FROM sextet_members WHERE sextet_id = sid;
      SELECT user_id INTO leader FROM sextet_members WHERE sextet_id = sid AND slot = 0;
      IF n <> 6 OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Six members and Trio A administrative leader required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER sextet_complete AFTER INSERT ON sextets
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_composition();
    CREATE CONSTRAINT TRIGGER member_complete AFTER INSERT OR UPDATE OR DELETE ON sextet_members
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_composition();

    CREATE FUNCTION protect_membership() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE state text;
    BEGIN
      IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'Composition is immutable' USING ERRCODE = '23514'; END IF;
      IF TG_OP = 'UPDATE' AND (NEW.sextet_id, NEW.slot, NEW.user_id) IS DISTINCT FROM
                             (OLD.sextet_id, OLD.slot, OLD.user_id) THEN
        RAISE EXCEPTION 'Composition is immutable' USING ERRCODE = '23514';
      END IF;
      SELECT r.status INTO state FROM allocation_rounds r JOIN sextets s ON s.round_id = r.id
        WHERE s.id = NEW.sextet_id;
      IF NEW.active IS DISTINCT FROM (state <> 'ARCHIVED') THEN
        RAISE EXCEPTION 'Membership activity must match round lifecycle' USING ERRCODE = '23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER membership_guard BEFORE INSERT OR UPDATE OR DELETE ON sextet_members
      FOR EACH ROW EXECUTE FUNCTION protect_membership();

    CREATE FUNCTION freeze_round_staff() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE state text;
    BEGIN
      SELECT status INTO state FROM allocation_rounds WHERE id = COALESCE(NEW.round_id, OLD.round_id) FOR UPDATE;
      IF state <> 'DRAFT' THEN RAISE EXCEPTION 'Eligible staff are frozen' USING ERRCODE = '23514'; END IF;
      RETURN COALESCE(NEW, OLD);
    END $$;
    CREATE TRIGGER staff_frozen BEFORE INSERT OR UPDATE OR DELETE ON round_staff
      FOR EACH ROW EXECUTE FUNCTION freeze_round_staff();

    CREATE FUNCTION validate_ranking() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; rid uuid; expected integer; actual integer; last_position integer;
    BEGIN
      sid := COALESCE(NEW.sextet_id, OLD.sextet_id);
      SELECT round_id INTO rid FROM preference_submissions WHERE sextet_id = sid;
      IF rid IS NULL THEN RETURN NULL; END IF;
      SELECT count(*) INTO expected FROM round_staff WHERE round_id = rid;
      SELECT count(*), max(position) INTO actual, last_position FROM preference_items WHERE sextet_id = sid;
      IF actual <> expected OR last_position IS DISTINCT FROM expected THEN
        RAISE EXCEPTION 'Ranking must be a complete permutation' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER submission_complete AFTER INSERT OR UPDATE ON preference_submissions
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_ranking();
    CREATE CONSTRAINT TRIGGER ranking_complete AFTER INSERT OR UPDATE OR DELETE ON preference_items
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_ranking();

    CREATE FUNCTION protect_round() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.status <> 'DRAFT' AND
         (NEW.name, NEW.registration_opens_at, NEW.registration_closes_at, NEW.preferences_open_at, NEW.preferences_close_at)
         IS DISTINCT FROM
         (OLD.name, OLD.registration_opens_at, OLD.registration_closes_at, OLD.preferences_open_at, OLD.preferences_close_at)
      THEN RAISE EXCEPTION 'Open round configuration is frozen' USING ERRCODE = '23514'; END IF;
      IF NEW.status <> OLD.status AND NOT (
        (OLD.status = 'DRAFT' AND NEW.status = 'OPEN') OR
        (OLD.status = 'OPEN' AND NEW.status = 'PROCESSED') OR
        (OLD.status = 'PROCESSED' AND NEW.status = 'PUBLISHED') OR
        (OLD.status = 'PUBLISHED' AND NEW.status = 'ARCHIVED'))
      THEN RAISE EXCEPTION 'Invalid round transition' USING ERRCODE = '23514'; END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER round_guard BEFORE UPDATE ON allocation_rounds
      FOR EACH ROW EXECUTE FUNCTION protect_round();
    """)


def downgrade():
    for function in [
        "protect_round",
        "validate_ranking",
        "freeze_round_staff",
        "protect_membership",
        "validate_composition",
        "reject_change",
    ]:
        op.execute(f"DROP FUNCTION {function}() CASCADE")
