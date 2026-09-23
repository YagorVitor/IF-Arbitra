"""Require consecutive member slots for flexible groups."""

from alembic import op

revision = "0009_group_slots"
down_revision = "0008_flexible_groups"
branch_labels = depends_on = None


def upgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION validate_composition() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; n integer; highest integer; leader uuid; creator uuid; expected integer;
    BEGIN
      IF TG_TABLE_NAME = 'sextets' THEN sid := NEW.id; ELSE sid := COALESCE(NEW.sextet_id, OLD.sextet_id); END IF;
      SELECT created_by, member_count INTO creator, expected FROM sextets WHERE id = sid;
      IF creator IS NULL THEN RETURN NULL; END IF;
      SELECT count(*), max(slot) INTO n, highest FROM sextet_members WHERE sextet_id = sid;
      SELECT user_id INTO leader FROM sextet_members WHERE sextet_id = sid AND slot = 0;
      IF n NOT BETWEEN 3 AND 6 OR n <> expected OR highest IS DISTINCT FROM expected - 1
         OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Complete group and administrative leader required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    """)


def downgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION validate_composition() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; n integer; leader uuid; creator uuid; expected integer;
    BEGIN
      IF TG_TABLE_NAME = 'sextets' THEN sid := NEW.id; ELSE sid := COALESCE(NEW.sextet_id, OLD.sextet_id); END IF;
      SELECT created_by, member_count INTO creator, expected FROM sextets WHERE id = sid;
      IF creator IS NULL THEN RETURN NULL; END IF;
      SELECT count(*) INTO n FROM sextet_members WHERE sextet_id = sid;
      SELECT user_id INTO leader FROM sextet_members WHERE sextet_id = sid AND slot = 0;
      IF n NOT BETWEEN 3 AND 6 OR n <> expected OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Complete group and administrative leader required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    """)
