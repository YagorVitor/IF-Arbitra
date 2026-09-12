from uuid import UUID

import pytest
from sqlalchemy import func, select, text

from app.db.migrations import migration_config
from app.db.models import (
    AllocationRound,
    InstitutionalStaff,
)

pytestmark = pytest.mark.integration


def test_seed_idempotent_and_names_preserved(world):
    from app.commands.seed import STAFF, seed

    seed()
    with world.db.begin() as db:
        db.get(InstitutionalStaff, UUID(STAFF[0][0])).name = "Nome corrigido"
    seed()
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(InstitutionalStaff)) == 17
        assert db.get(InstitutionalStaff, UUID(STAFF[0][0])).name == "Nome corrigido"


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
        assert db.scalar(text("SELECT version_num FROM alembic_version")) == "0004_run_history"
        assert db.scalar(select(func.count()).select_from(AllocationRound)) == 1
