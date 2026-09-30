import pytest
from sqlalchemy import select

from app.core.security import hasher
from app.db.models import AuditEvent, LoginSession, User
from tests.support import as_user

pytestmark = pytest.mark.integration


def test_restore_reserved_test_login_and_issue_manual_access(world, client):
    student = world.users[0]
    with world.db.begin() as db:
        row = db.get(User, student.id)
        row.login = row.email = "qa-aluno-01@if-arbitra.invalid"
        row.active = False
        row.removed_at = world.now
    restore = f"/api/admin/students/{student.id}/restore"
    access = f"/api/admin/students/{student.id}/access"
    as_user(client, world.users[1])
    assert client.post(restore).status_code == 403
    assert client.post(access).status_code == 403
    as_user(client, world.admin)
    assert client.post(access).status_code == 404
    assert client.post(restore).status_code == 200
    response = client.post(access)
    assert response.status_code == 200, response.text
    credential = response.json()
    assert credential["login"] == "qa-aluno-01@if-arbitra.invalid"
    assert len(credential["password"]) >= 20
    assert response.headers["Cache-Control"] == "no-store"
    with world.db() as db:
        row = db.get(User, student.id)
        assert row.active and row.removed_at is None
        assert hasher.verify(row.password_hash, credential["password"])
        assert db.scalar(select(LoginSession).where(LoginSession.user_id == student.id)) is None
        for audit in db.scalars(select(AuditEvent)):
            assert credential["password"] not in str(audit.payload)
            assert credential["password"] not in str(audit.resulting_state)
    client.cookies.clear()
    login = client.post("/api/auth/login", json=credential)
    assert login.status_code == 200, login.text
    assert client.get("/api/rounds").status_code == 200
