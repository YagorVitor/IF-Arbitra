import json
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.models import (
    AuditEvent,
    LoginThrottle,
)

pytestmark = pytest.mark.integration


def test_auth_csrf_and_privacy(world, client):
    assert client.get("/api/rounds").status_code == 401
    assert (
        client.post(
            "/api/auth/login",
            headers={"Origin": "https://evil.invalid"},
            json={"login": "admin", "password": "testing-password-2026"},
        ).status_code
        == 403
    )
    response = client.post(
        "/api/auth/login", json={"login": "admin", "password": "testing-password-2026"}
    )
    assert response.status_code == 200, response.text
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "password_hash" not in response.text
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post("/api/auth/login", json={"login": "admin", "password": "incorrect"}).status_code
        == 401
    )
    with world.db() as db:
        payloads = json.dumps([e.payload for e in db.scalars(select(AuditEvent))])
        assert "incorrect" not in payloads and "testing-password" not in payloads


def test_login_limit_resets_at_deadline_and_survives_new_clients(world, client):
    from app.core.security import digest

    for _ in range(10):
        assert (
            client.post(
                "/api/auth/login", json={"login": "absent", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post("/api/auth/login", json={"login": "absent", "password": "wrong"}).status_code
        == 429
    )
    with world.db.begin() as db:
        db.get(LoginThrottle, digest("login:absent")).expires_at = world.now - timedelta(seconds=1)
    assert (
        client.post("/api/auth/login", json={"login": "absent", "password": "wrong"}).status_code
        == 401
    )
    with world.db() as db:
        assert db.get(LoginThrottle, digest("login:absent")).count == 1
