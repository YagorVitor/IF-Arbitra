"""Six mandatory members including captain, seventh optional; keep historic formats."""

import sqlalchemy as sa
from alembic import op

revision = "0012_groups_seven"
down_revision = "0011_admin_adjustments"
branch_labels = depends_on = None


def composition(maximum, groups):
    group_check = "OR (mode = 'GROUPS' AND n NOT IN (6, 7))" if groups else ""
    return f"""
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
      IF n NOT BETWEEN 3 AND {maximum} OR n <> expected OR highest IS DISTINCT FROM expected - 1
         OR (mode = 'TRIOS' AND n <> 3) OR (mode = 'SEXTET' AND n > 6)
         {group_check} OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Complete group and captain required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    """


def upgrade():
    op.drop_constraint("ck_round_formation_mode", "allocation_rounds", type_="check")
    op.create_check_constraint(
        "ck_round_formation_mode",
        "allocation_rounds",
        "formation_mode IN ('SEXTET','TRIOS','GROUPS')",
    )
    op.alter_column("allocation_rounds", "formation_mode", server_default="GROUPS")
    op.drop_constraint("ck_sextets_member_count", "sextets", type_="check")
    op.create_check_constraint("ck_sextets_member_count", "sextets", "member_count BETWEEN 3 AND 7")
    op.drop_constraint("sextet_members_slot_check", "sextet_members", type_="check")
    op.create_check_constraint("ck_member_slot", "sextet_members", "slot BETWEEN 0 AND 6")
    op.execute(composition(7, True))


def downgrade():
    if op.get_bind().scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM allocation_rounds WHERE formation_mode = 'GROUPS')")
    ):
        raise RuntimeError("Migrate group rounds before downgrading")
    op.execute(composition(6, False))
    op.drop_constraint("ck_member_slot", "sextet_members", type_="check")
    op.create_check_constraint(
        "sextet_members_slot_check", "sextet_members", "slot BETWEEN 0 AND 5"
    )
    op.drop_constraint("ck_sextets_member_count", "sextets", type_="check")
    op.create_check_constraint("ck_sextets_member_count", "sextets", "member_count BETWEEN 3 AND 6")
    op.drop_constraint("ck_round_formation_mode", "allocation_rounds", type_="check")
    op.create_check_constraint(
        "ck_round_formation_mode", "allocation_rounds", "formation_mode IN ('SEXTET','TRIOS')"
    )
    op.alter_column("allocation_rounds", "formation_mode", server_default="TRIOS")
