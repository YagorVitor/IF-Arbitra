"""Allow student groups of three to six members."""

import sqlalchemy as sa
from alembic import op

revision = "0008_flexible_groups"
down_revision = "0007_initial_roster"
branch_labels = depends_on = None


def _composition_function(allow_flexible):
    count_check = "n NOT BETWEEN 3 AND 6 OR n <> expected" if allow_flexible else "n <> 6"
    expected_declaration = "expected integer;" if allow_flexible else ""
    expected_selection = (
        "SELECT created_by, member_count INTO creator, expected FROM sextets WHERE id = sid;"
        if allow_flexible
        else "SELECT created_by INTO creator FROM sextets WHERE id = sid;"
    )
    return f"""
    CREATE OR REPLACE FUNCTION validate_composition() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sid uuid; n integer; leader uuid; creator uuid; {expected_declaration}
    BEGIN
      IF TG_TABLE_NAME = 'sextets' THEN sid := NEW.id; ELSE sid := COALESCE(NEW.sextet_id, OLD.sextet_id); END IF;
      {expected_selection}
      IF creator IS NULL THEN RETURN NULL; END IF;
      SELECT count(*) INTO n FROM sextet_members WHERE sextet_id = sid;
      SELECT user_id INTO leader FROM sextet_members WHERE sextet_id = sid AND slot = 0;
      IF {count_check} OR leader IS DISTINCT FROM creator THEN
        RAISE EXCEPTION 'Complete group and administrative leader required' USING ERRCODE = '23514';
      END IF;
      IF EXISTS (SELECT 1 FROM sextet_members m JOIN users u ON u.id = m.user_id
                 WHERE m.sextet_id = sid AND u.role <> 'STUDENT') THEN
        RAISE EXCEPTION 'Members must be students' USING ERRCODE = '23514';
      END IF;
      RETURN NULL;
    END $$;
    """


def upgrade():
    op.add_column(
        "sextets",
        sa.Column("member_count", sa.Integer(), server_default="6", nullable=False),
    )
    op.create_check_constraint("ck_sextets_member_count", "sextets", "member_count BETWEEN 3 AND 6")
    op.execute(_composition_function(True))


def downgrade():
    if op.get_bind().scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM sextets WHERE member_count <> 6)")
    ):
        raise RuntimeError("Archive or migrate smaller groups before downgrading")
    op.execute(_composition_function(False))
    op.drop_constraint("ck_sextets_member_count", "sextets", type_="check")
    op.drop_column("sextets", "member_count")
