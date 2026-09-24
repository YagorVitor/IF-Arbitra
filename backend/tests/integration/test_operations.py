from uuid import NAMESPACE_URL, uuid5

import pytest
from sqlalchemy import func, select, text

from app.db.migrations import migration_config
from app.db.models import (
    AllocationRound,
    InstitutionalStaff,
    User,
)

pytestmark = pytest.mark.integration


def test_seed_idempotent_and_names_preserved(world):
    from app.commands.seed import seed

    staff_id = uuid5(NAMESPACE_URL, "if-arbitra:test-staff")
    roster = {
        "staff": [{"id": str(staff_id), "name": "Servidor inicial", "email": "staff@example.org"}],
        "students": [{"name": "Aluno inicial", "email": "student@example.org"}],
    }
    seed(roster)
    with world.db.begin() as db:
        db.get(InstitutionalStaff, staff_id).name = "Nome corrigido"
        db.get(InstitutionalStaff, staff_id).active = False
        first_student = db.scalar(select(User).where(User.email == "student@example.org"))
        first_student.removed_at = world.now
    seed(roster)
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(InstitutionalStaff)) == 4
        assert db.get(InstitutionalStaff, staff_id).name == "Nome corrigido"
        assert not db.get(InstitutionalStaff, staff_id).active
        assert db.get(InstitutionalStaff, staff_id).email
        assert db.scalar(select(func.count()).select_from(User).where(User.email.is_not(None))) == 1
        assert db.scalar(select(User).where(User.email == "student@example.org")).removed_at


def test_wrong_migration_is_not_ready(world, client):
    with world.db.begin() as db:
        db.execute(text("UPDATE alembic_version SET version_num='obsolete'"))
    assert client.get("/ready").status_code == 503
    assert client.get("/health").status_code == 200


def test_run_history_migration_roundtrip(world):

    from alembic import command

    config = migration_config()
    command.downgrade(config, "0003_audit_context")
    command.upgrade(config, "head")
    with world.db() as db:
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0009_group_slots"
        assert db.scalar(select(func.count()).select_from(AllocationRound)) == 1
