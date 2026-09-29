"""Keep legacy sextet rounds and allow two registered trios per server."""

import sqlalchemy as sa
from alembic import op

revision = "0010_trio_formation"
down_revision = "0009_group_slots"
branch_labels = depends_on = None


def upgrade():
    op.add_column(
        "allocation_rounds",
        sa.Column("formation_mode", sa.String(16), server_default="SEXTET", nullable=False),
    )
    op.create_check_constraint(
        "ck_round_formation_mode",
        "allocation_rounds",
        "formation_mode IN ('SEXTET','TRIOS')",
    )
    op.alter_column("allocation_rounds", "formation_mode", server_default="TRIOS")
    op.add_column(
        "allocations",
        sa.Column("staff_slot", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_check_constraint(
        "ck_allocation_staff_slot", "allocations", "staff_slot BETWEEN 1 AND 2"
    )
    op.drop_constraint("allocations_round_id_staff_id_key", "allocations", type_="unique")
    op.create_unique_constraint(
        "uq_allocation_staff_slot", "allocations", ["round_id", "staff_id", "staff_slot"]
    )
    op.execute("""
    CREATE OR REPLACE FUNCTION validate_composition() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; n integer; highest integer; leader uuid; creator uuid;
            expected integer; mode text;
    BEGIN
      IF TG_TABLE_NAME = 'sextets' THEN sid := NEW.id; ELSE sid := COALESCE(NEW.sextet_id, OLD.sextet_id); END IF;
      SELECT s.created_by, s.member_count, r.formation_mode
        INTO creator, expected, mode
        FROM sextets s JOIN allocation_rounds r ON r.id = s.round_id WHERE s.id = sid;
      IF creator IS NULL THEN RETURN NULL; END IF;
      SELECT count(*), max(slot) INTO n, highest FROM sextet_members WHERE sextet_id = sid;
      SELECT user_id INTO leader FROM sextet_members WHERE sextet_id = sid AND slot = 0;
      IF n NOT BETWEEN 3 AND 6 OR n <> expected OR highest IS DISTINCT FROM expected - 1
         OR (mode = 'TRIOS' AND n <> 3) OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Complete group and administrative leader required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    CREATE OR REPLACE FUNCTION protect_round() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.status <> 'DRAFT' AND
         (NEW.name, NEW.formation_mode, NEW.registration_opens_at,
          NEW.registration_closes_at, NEW.preferences_open_at, NEW.preferences_close_at)
         IS DISTINCT FROM
         (OLD.name, OLD.formation_mode, OLD.registration_opens_at,
          OLD.registration_closes_at, OLD.preferences_open_at, OLD.preferences_close_at)
      THEN RAISE EXCEPTION 'Open round configuration is frozen' USING ERRCODE = '23514'; END IF;
      IF NEW.status <> OLD.status AND NOT (
        (OLD.status = 'DRAFT' AND NEW.status = 'OPEN') OR
        (OLD.status = 'OPEN' AND NEW.status = 'PROCESSED') OR
        (OLD.status = 'PROCESSED' AND NEW.status = 'PUBLISHED') OR
        (OLD.status = 'PUBLISHED' AND NEW.status = 'ARCHIVED'))
      THEN RAISE EXCEPTION 'Invalid round transition' USING ERRCODE = '23514'; END IF;
      RETURN NEW;
    END $$;
    CREATE FUNCTION validate_trio_pair() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE mode text; size integer;
    BEGIN
      IF NEW.staff_id IS NULL THEN RETURN NULL; END IF;
      SELECT formation_mode INTO mode FROM allocation_rounds WHERE id = NEW.round_id;
      IF mode <> 'TRIOS' THEN RETURN NULL; END IF;
      SELECT count(*) INTO size FROM allocations
        WHERE round_id = NEW.round_id AND staff_id = NEW.staff_id;
      IF size <> 2 THEN
        RAISE EXCEPTION 'A server must receive a complete pair of trios' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    CREATE CONSTRAINT TRIGGER allocation_trio_pair AFTER INSERT ON allocations
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_trio_pair();
    """)


def downgrade():
    bind = op.get_bind()
    if bind.scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM allocation_rounds WHERE formation_mode = 'TRIOS')")
    ):
        raise RuntimeError("Archive or migrate trio rounds before downgrading")
    if bind.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM allocations WHERE staff_slot = 2)")):
        raise RuntimeError("Trio allocations must be migrated before downgrading")
    op.execute("DROP TRIGGER allocation_trio_pair ON allocations")
    op.execute("DROP FUNCTION validate_trio_pair()")
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
    CREATE OR REPLACE FUNCTION protect_round() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      IF OLD.status <> 'DRAFT' AND
         (NEW.name, NEW.registration_opens_at, NEW.registration_closes_at,
          NEW.preferences_open_at, NEW.preferences_close_at)
         IS DISTINCT FROM
         (OLD.name, OLD.registration_opens_at, OLD.registration_closes_at,
          OLD.preferences_open_at, OLD.preferences_close_at)
      THEN RAISE EXCEPTION 'Open round configuration is frozen' USING ERRCODE = '23514'; END IF;
      IF NEW.status <> OLD.status AND NOT (
        (OLD.status = 'DRAFT' AND NEW.status = 'OPEN') OR
        (OLD.status = 'OPEN' AND NEW.status = 'PROCESSED') OR
        (OLD.status = 'PROCESSED' AND NEW.status = 'PUBLISHED') OR
        (OLD.status = 'PUBLISHED' AND NEW.status = 'ARCHIVED'))
      THEN RAISE EXCEPTION 'Invalid round transition' USING ERRCODE = '23514'; END IF;
      RETURN NEW;
    END $$;
    """)
    op.drop_constraint("uq_allocation_staff_slot", "allocations", type_="unique")
    op.create_unique_constraint(
        "allocations_round_id_staff_id_key", "allocations", ["round_id", "staff_id"]
    )
    op.drop_constraint("ck_allocation_staff_slot", "allocations", type_="check")
    op.drop_column("allocations", "staff_slot")
    op.drop_constraint("ck_round_formation_mode", "allocation_rounds", type_="check")
    op.drop_column("allocation_rounds", "formation_mode")
