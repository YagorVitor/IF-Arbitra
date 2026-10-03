"""Separate roster membership from captain login access."""

import sqlalchemy as sa
from alembic import op

revision = "0013_captain_access"
down_revision = "0012_groups_seven"
branch_labels = depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("is_captain", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("users", sa.Column("phone", sa.String(32), nullable=True))
    op.execute(
        "DELETE FROM login_sessions WHERE user_id IN (SELECT id FROM users WHERE role = 'STUDENT')"
    )
    op.execute("""
    CREATE OR REPLACE FUNCTION validate_composition() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; n integer; highest integer; leader uuid; creator uuid;
            expected integer; mode text;
    BEGIN
      IF TG_TABLE_NAME = 'sextets' THEN sid := NEW.id; ELSE sid := COALESCE(NEW.sextet_id, OLD.sextet_id); END IF;
      SELECT s.created_by, s.member_count, r.formation_mode INTO creator, expected, mode
        FROM sextets s JOIN allocation_rounds r ON r.id = s.round_id WHERE s.id = sid;
      IF creator IS NULL THEN RETURN NULL; END IF;
      SELECT count(*), max(slot) INTO n, highest FROM sextet_members WHERE sextet_id = sid;
      SELECT user_id INTO leader FROM sextet_members WHERE sextet_id = sid AND slot = 0;
      IF n NOT BETWEEN 3 AND 7 OR n <> expected OR highest IS DISTINCT FROM expected - 1
         OR (mode = 'TRIOS' AND n <> 3) OR (mode = 'SEXTET' AND n > 6)
         OR (mode = 'GROUPS' AND n NOT IN (6, 7)) OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Complete group and captain required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      IF mode = 'GROUPS' AND EXISTS (
          SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
          WHERE m.sextet_id = sid AND m.slot > 0 AND u.is_captain) THEN
        RAISE EXCEPTION 'Another captain cannot join a group' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    """)


def downgrade():
    op.execute("""
    CREATE OR REPLACE FUNCTION validate_composition() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; n integer; highest integer; leader uuid; creator uuid;
            expected integer; mode text;
    BEGIN
      IF TG_TABLE_NAME = 'sextets' THEN sid := NEW.id; ELSE sid := COALESCE(NEW.sextet_id, OLD.sextet_id); END IF;
      SELECT s.created_by, s.member_count, r.formation_mode INTO creator, expected, mode
        FROM sextets s JOIN allocation_rounds r ON r.id = s.round_id WHERE s.id = sid;
      IF creator IS NULL THEN RETURN NULL; END IF;
      SELECT count(*), max(slot) INTO n, highest FROM sextet_members WHERE sextet_id = sid;
      SELECT user_id INTO leader FROM sextet_members WHERE sextet_id = sid AND slot = 0;
      IF n NOT BETWEEN 3 AND 7 OR n <> expected OR highest IS DISTINCT FROM expected - 1
         OR (mode = 'TRIOS' AND n <> 3) OR (mode = 'SEXTET' AND n > 6)
         OR (mode = 'GROUPS' AND n NOT IN (6, 7)) OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Complete group and captain required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    """)
    op.drop_column("users", "phone")
    op.drop_column("users", "is_captain")
