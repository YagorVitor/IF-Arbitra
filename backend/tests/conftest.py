import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

url = os.environ.get("TEST_DATABASE_URL")
if url:
    if not make_url(url).database.endswith("_test"):
        raise RuntimeError("TEST_DATABASE_URL must name a dedicated database ending in _test")
    os.environ["DATABASE_URL"] = url
os.environ["ENVIRONMENT"] = "development"


@pytest.fixture
def world():
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
    from app.auth import digest, hasher
    from app.db import SessionFactory, engine
    from app.models import AllocationRound, InstitutionalStaff, LoginSession, RoundStaff, User

    engine.dispose()
    with engine.begin() as conn:
        assert conn.scalar(text("select current_database()")).endswith("_test")
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")
    now = datetime.now(UTC)
    with SessionFactory.begin() as db:
        password_hash = hasher.hash("testing-password-2026")
        users = [
            User(name=f"Aluno teste {i:02}", login=f"student{i}", password_hash=password_hash)
            for i in range(24)
        ]
        admin = User(name="Admin teste", login="admin", role="ADMIN", password_hash=password_hash)
        db.add_all([*users, admin])
        staff = [InstitutionalStaff(name=n) for n in ["A", "B", "C"]]
        db.add_all(staff)
        r = AllocationRound(
            name="Rodada de teste",
            registration_opens_at=now - timedelta(hours=1),
            registration_closes_at=now + timedelta(hours=1),
            preferences_open_at=now - timedelta(hours=1),
            preferences_close_at=now + timedelta(hours=2),
        )
        db.add(r)
        db.flush()
        db.add_all([RoundStaff(round_id=r.id, staff_id=s.id, order=i) for i, s in enumerate(staff)])
        db.flush()
        r.status = "OPEN"
        for u in [*users, admin]:
            db.add(
                LoginSession(
                    token_hash=digest(str(u.id)), user_id=u.id, expires_at=now + timedelta(days=1)
                )
            )
    return SimpleNamespace(
        users=users, admin=admin, staff=staff, round=r, now=now, db=SessionFactory
    )


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(
        app, raise_server_exceptions=False, headers={"Origin": "http://localhost:5173"}
    ) as c:
        yield c


def as_user(client, user):
    client.cookies.set("if_arbitra_session", str(user.id))
    return client


def register(client, world, indices=range(6), key=None):
    students = [world.users[i] for i in indices]
    as_user(client, students[0])
    return client.post(
        f"/api/rounds/{world.round.id}/sextets",
        json={
            "name": "Sexteto teste",
            "members": [str(s.id) for s in students],
            "idempotency_key": str(key or uuid4()),
        },
    )
