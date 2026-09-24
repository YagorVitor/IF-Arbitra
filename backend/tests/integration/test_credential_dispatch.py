"""Credentials are sent only by an explicit administrator action."""

import json
from types import SimpleNamespace
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.errors import DomainError
from app.db.models import AuditEvent, User
from tests.support import as_user

pytestmark = pytest.mark.integration


def configured(monkeypatch, sent):
    monkeypatch.setattr(
        "app.services.credential_dispatch.settings",
        lambda: SimpleNamespace(
            smtp_host="smtp.test",
            smtp_port=587,
            smtp_from="IF-Arbitra <noreply@test.invalid>",
            smtp_starttls=True,
            smtp_username=None,
            smtp_password=None,
        ),
    )
    monkeypatch.setattr(
        "app.services.credential_dispatch._send_credentials",
        lambda address, password: sent.append((address, password)),
    )


def test_admin_dispatches_equal_length_credentials_once(world, client, monkeypatch):
    sent = []
    configured(monkeypatch, sent)
    as_user(client, world.admin)
    for address in ("Primeiro@Example.org", "segundo@example.org"):
        created = client.post("/api/admin/students", json={"name": "Aluno Novo", "email": address})
        assert created.status_code == 201, created.text
        assert created.json()["login"] == address.casefold()
    client.cookies.clear()
    assert client.post("/api/admin/students/dispatch-credentials").status_code == 401
    as_user(client, world.users[0])
    assert client.post("/api/admin/students/dispatch-credentials").status_code == 403
    as_user(client, world.admin)
    result = client.post("/api/admin/students/dispatch-credentials")
    assert result.status_code == 200, result.text
    assert result.json()["eligible"] == result.json()["sent"] == 2
    assert result.json()["failed"] == []
    assert result.json()["pending_remaining"] == 0
    assert {address for address, _ in sent} == {
        "primeiro@example.org",
        "segundo@example.org",
    }
    assert len({password for _, password in sent}) == 2
    assert {len(password) for _, password in sent} == {8}
    assert client.post("/api/admin/students/dispatch-credentials").json()["sent"] == 0
    assert len(sent) == 2
    for address, password in sent:
        with world.db() as db:
            student = db.scalar(select(User).where(User.email == address))
            assert student.login == address and student.active
            assert student.password_hash and password not in student.password_hash
        login = client.post("/api/auth/login", json={"login": address, "password": password})
        assert login.status_code == 200, login.text
    assert client.post("/api/auth/email-verification/request", json={}).status_code == 404
    assert client.post("/api/auth/set-password", json={}).status_code == 404
    with world.db() as db:
        events = list(db.scalars(select(AuditEvent)))
        assert sum(e.event_type == "CREDENTIAL_DISPATCHED" for e in events) == 2
        serialized = json.dumps([(e.payload, e.previous_state, e.resulting_state) for e in events])
        assert all(password not in serialized for _, password in sent)


def test_failed_delivery_remains_pending_and_can_be_retried(world, client, monkeypatch):
    sent = []
    configured(monkeypatch, sent)
    as_user(client, world.admin)
    student_id = client.post(
        "/api/admin/students", json={"name": "Aluno Novo", "email": "retry@example.org"}
    ).json()["id"]
    original = __import__("app.services.credential_dispatch", fromlist=["_send_credentials"])

    def fail_once(address, password):
        if not sent:
            sent.append((address, password))
            raise DomainError("EMAIL_UNAVAILABLE", "SMTP indisponível", 503)
        sent.append((address, password))

    monkeypatch.setattr(original, "_send_credentials", fail_once)
    first = client.post("/api/admin/students/dispatch-credentials")
    assert first.status_code == 200, first.text
    assert first.json()["sent"] == 0
    assert first.json()["failed"] == [{"email": "retry@example.org", "code": "EMAIL_UNAVAILABLE"}]
    assert first.json()["pending_remaining"] == 1
    with world.db() as db:
        user = db.get(User, UUID(student_id))
        assert not user.active and user.password_hash is None
    second = client.post("/api/admin/students/dispatch-credentials")
    assert second.status_code == 200, second.text
    assert second.json()["sent"] == 1
    assert second.json()["failed"] == []
    assert second.json()["pending_remaining"] == 0
    assert sent[0][1] != sent[1][1]
    with world.db() as db:
        assert db.get(User, UUID(student_id)).active
        assert db.scalar(
            select(AuditEvent).where(AuditEvent.event_type == "CREDENTIAL_DELIVERY_FAILED")
        )


def test_legacy_pending_login_becomes_email_on_dispatch(world, client, monkeypatch):
    sent = []
    configured(monkeypatch, sent)
    with world.db.begin() as db:
        db.add(
            User(
                name="Aluno antigo",
                login="legacy-login",
                email="legacy@example.org",
                password_hash=None,
                active=False,
            )
        )
    as_user(client, world.admin)
    response = client.post("/api/admin/students/dispatch-credentials")
    assert response.status_code == 200, response.text
    assert response.json()["sent"] == 1
    with world.db() as db:
        user = db.scalar(select(User).where(User.email == "legacy@example.org"))
        assert user.login == user.email
