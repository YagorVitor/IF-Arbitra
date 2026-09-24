"""Administrators manage the seeded roster without deleting round history."""

from types import SimpleNamespace
from uuid import UUID

import pytest
from sqlalchemy import select

from app.db.models import User
from tests.support import as_user, register

pytestmark = pytest.mark.integration


def test_student_removal_skips_dispatch_and_readdition_issues_new_credentials(
    world, client, monkeypatch
):
    sent = []
    monkeypatch.setattr(
        "app.services.credential_dispatch.settings",
        lambda: SimpleNamespace(smtp_host="smtp.test", smtp_from="noreply@example.org"),
    )
    monkeypatch.setattr(
        "app.services.credential_dispatch._send_credentials",
        lambda address, password: sent.append((address, password)),
    )
    as_user(client, world.admin)
    response = client.post(
        "/api/admin/students", json={"name": "Aluno Adicional", "email": "extra@example.org"}
    )
    assert response.status_code == 201, response.text
    student_id = response.json()["id"]
    listed = client.get("/api/admin/students").json()
    assert any(student["id"] == student_id for student in listed)
    assert client.delete(f"/api/admin/students/{student_id}").status_code == 204
    assert all(student["id"] != student_id for student in client.get("/api/admin/students").json())
    removed = client.get("/api/admin/students", params={"include_removed": True}).json()
    assert next(student for student in removed if student["id"] == student_id)["removed_at"]
    assert client.post("/api/admin/students/dispatch-credentials").json()["eligible"] == 0
    assert not sent
    restored = client.post(
        "/api/admin/students", json={"name": "Nome Corrigido", "email": "EXTRA@example.org"}
    )
    assert restored.status_code == 201, restored.text
    assert restored.json()["id"] == student_id
    assert client.post("/api/admin/students/dispatch-credentials").json()["sent"] == 1
    assert len(sent[0][1]) == 8
    login = client.post(
        "/api/auth/login", json={"login": "extra@example.org", "password": sent[0][1]}
    )
    assert login.status_code == 200, login.text
    client.cookies.clear()
    as_user(client, world.admin)
    assert client.delete(f"/api/admin/students/{student_id}").status_code == 204
    assert (
        client.post(
            "/api/auth/login", json={"login": "extra@example.org", "password": sent[0][1]}
        ).status_code
        == 401
    )
    with world.db() as db:
        assert db.get(User, UUID(student_id)).removed_at is not None


def test_cannot_remove_student_in_active_sextet(world, client):
    register(client, world)
    as_user(client, world.admin)
    response = client.delete(f"/api/admin/students/{world.users[0].id}")
    assert response.status_code == 409
    assert response.json()["code"] == "STUDENT_IN_SEXTET"
    with world.db() as db:
        assert db.scalar(select(User).where(User.id == world.users[0].id)).active


def test_staff_add_remove_restore_and_active_round_guard(world, client):
    as_user(client, world.admin)
    response = client.post(
        "/api/admin/staff",
        json={"name": "Servidor Adicional", "email": "staff.extra@ifsp.edu.br"},
    )
    assert response.status_code == 201, response.text
    staff_id = response.json()["id"]
    assert response.json()["email"] == "staff.extra@ifsp.edu.br"
    assert client.delete(f"/api/admin/staff/{staff_id}").status_code == 204
    assert (
        next(s for s in client.get("/api/staff").json() if s["id"] == staff_id)["active"] is False
    )
    restored = client.post(
        "/api/admin/staff",
        json={"name": "Servidor Corrigido", "email": "STAFF.EXTRA@ifsp.edu.br"},
    )
    assert restored.status_code == 201, restored.text
    assert restored.json()["id"] == staff_id
    assert client.delete(f"/api/admin/staff/{world.staff[0].id}").status_code == 204
    frozen = client.get(f"/api/rounds/{world.round.id}").json()
    assert str(world.staff[0].id) in [item["id"] for item in frozen["staff"]]
    as_user(client, world.users[0])
    assert client.get("/api/admin/students").status_code == 403
    assert client.delete(f"/api/admin/staff/{staff_id}").status_code == 403
