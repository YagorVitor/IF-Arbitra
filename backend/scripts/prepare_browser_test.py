"""Explicit opt-in test fixture. Never usable against a production/non-test database."""

import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.engine import make_url

if os.environ.get("ENVIRONMENT", "development") != "development":
    raise RuntimeError("Browser fixtures require development environment")
if not make_url(os.environ["DATABASE_URL"]).database.endswith("_test"):
    raise RuntimeError("Browser fixtures require a dedicated database ending in _test")

from app.auth import hasher
from app.db import SessionFactory
from app.models import AllocationRound, RoundStaff, User
from app.seed import STAFF, seed

seed()
password = secrets.token_urlsafe(24)
now = datetime.now(UTC)
with SessionFactory.begin() as db:
    users = [
        User(
            name=f"Aluno de validação {i:02}",
            login=f"qa-aluno-{i:02}",
            password_hash=hasher.hash(password),
        )
        for i in range(12)
    ]
    admin = User(
        name="Administração de validação",
        login="qa-admin",
        role="ADMIN",
        password_hash=hasher.hash(password),
    )
    db.add_all([*users, admin])
    round_ = AllocationRound(
        name="Validação local · dados de teste",
        registration_opens_at=now - timedelta(hours=1),
        registration_closes_at=now + timedelta(minutes=7),
        preferences_open_at=now - timedelta(hours=1),
        preferences_close_at=now + timedelta(minutes=8),
    )
    db.add(round_)
    db.flush()
    from uuid import UUID

    db.add_all(
        [RoundStaff(round_id=round_.id, staff_id=UUID(s[0]), order=i) for i, s in enumerate(STAFF)]
    )
    db.flush()
    round_.status = "OPEN"
    data = {
        "password": password,
        "admin_login": admin.login,
        "student_login": users[0].login,
        "round_id": str(round_.id),
        "students": [str(u.id) for u in users],
        "preferences_close_at": round_.preferences_close_at.isoformat(),
    }
target = Path(os.environ["BROWSER_FIXTURE_OUTPUT"])
target.write_text(json.dumps(data), encoding="utf-8")
print("Fixture de navegador criada; credenciais somente no arquivo local indicado.")
