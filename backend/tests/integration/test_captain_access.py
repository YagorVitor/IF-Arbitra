from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.db.models import LoginSession, User
from tests.integration.test_credential_dispatch import configured
from tests.support import as_user, draft_payload

pytestmark = pytest.mark.integration


def setup_roster(world, client):
    with world.db.begin() as db:
        for i, row in enumerate(world.users):
            u = db.get(User, row.id)
            u.is_captain = i in (0, 1)
            if i >= 2:
                u.active = False
                u.password_hash = None
    as_user(client, world.admin)
    response = client.post(
        "/api/admin/rounds", json={**draft_payload(world), "formation_mode": "GROUPS"}
    )
    assert response.status_code == 201, response.text
    rid = response.json()["id"]
    assert (
        client.post(f"/api/admin/rounds/{rid}/transition", json={"action": "open"}).status_code
        == 200
    )
    return rid


def payload(world, indices):
    return {
        "name": "Grupo do capitão",
        "members": [str(world.users[i].id) for i in indices],
        "idempotency_key": str(uuid4()),
    }


def test_captains_cannot_capture_each_other_and_members_need_no_login(world, client):
    rid = setup_roster(world, client)
    as_user(client, world.users[0])
    search = client.get("/api/students", params={"q": "Aluno teste"})
    assert search.status_code == 200
    ids = {row["id"] for row in search.json()}
    assert str(world.users[0].id) not in ids and str(world.users[1].id) not in ids
    assert str(world.users[2].id) in ids  # Inactive login, eligible roster member.
    rejected = client.post(f"/api/rounds/{rid}/sextets", json=payload(world, [0, 1, 2, 3, 4, 5]))
    assert rejected.status_code == 409 and rejected.json()["code"] == "CAPTAIN_AS_MEMBER"
    assert client.get(f"/api/rounds/{rid}/my-sextet").json() is None
    first = client.post(f"/api/rounds/{rid}/sextets", json=payload(world, [0, 2, 3, 4, 5, 6]))
    assert first.status_code == 201, first.text
    as_user(client, world.users[1])
    second = client.post(f"/api/rounds/{rid}/sextets", json=payload(world, [1, 7, 8, 9, 10, 11]))
    assert second.status_code == 201, second.text
    assert len(second.json()["members"]) == 6
    # Changing a member into a captain must not invalidate the existing composition.
    as_user(client, world.admin)
    response = client.put(
        f"/api/admin/students/{world.users[2].id}/captain", json={"is_captain": True}
    )
    assert response.status_code == 409


def test_non_captain_with_old_password_and_session_cannot_enter(world, client):
    with world.db.begin() as db:
        db.get(User, world.users[2].id).is_captain = False
    as_user(client, world.users[2])
    assert client.get("/api/auth/me").status_code == 403
    assert client.get("/api/rounds").status_code == 403
    response = client.post(
        "/api/auth/login", json={"login": world.users[2].login, "password": "testing-password-2026"}
    )
    assert response.status_code == 403 and response.json()["code"] == "CAPTAIN_REQUIRED"
    response = client.post(
        "/api/auth/login", json={"login": world.users[2].login, "password": "wrong"}
    )
    assert response.status_code == 401
    as_user(client, world.admin)
    assert client.post(f"/api/admin/students/{world.users[2].id}/access").status_code == 403


def test_only_captains_receive_credentials_and_role_changes_revoke_access(
    world, client, monkeypatch
):
    sent = []
    configured(monkeypatch, sent)
    monkeypatch.setattr(
        "app.services.credential_dispatch._send_credentials",
        lambda address, password, name: sent.append((address, password, name)),
    )
    as_user(client, world.admin)
    ordinary = client.post(
        "/api/admin/students", json={"name": "Integrante sem login", "email": "member@example.org"}
    ).json()
    captain = client.post(
        "/api/admin/students",
        json={
            "name": "Capitã cadastrada",
            "email": "captain@example.org",
            "is_captain": True,
            "phone": "(16) 99999-9999",
        },
    ).json()
    response = client.post("/api/admin/students/dispatch-credentials")
    assert response.status_code == 200 and response.json()["sent"] == 1
    assert sent[0][0] == "captain@example.org"
    assert sent[0][2] == "Capitã cadastrada"
    assert client.post(f"/api/admin/students/{ordinary['id']}/access").status_code == 403
    login = client.post("/api/auth/login", json={"login": sent[0][0], "password": sent[0][1]})
    assert login.status_code == 200 and login.json()["is_captain"] is True
    old_token = login.cookies.get("if_arbitra_session")
    client.cookies.clear()
    as_user(client, world.admin)
    assert (
        client.put(
            f"/api/admin/students/{captain['id']}/captain", json={"is_captain": False}
        ).status_code
        == 200
    )
    with world.db() as db:
        row = db.get(User, UUID(captain["id"]))
        assert not row.active and row.password_hash is None
        assert not db.scalar(select(LoginSession).where(LoginSession.user_id == row.id))
    client.cookies.clear()
    client.cookies.set("if_arbitra_session", old_token)
    assert client.get("/api/auth/me").status_code == 401


def test_captain_contact_update_is_admin_only_and_preserves_identity(world, client):
    captain = world.users[0]
    body = {"name": "Nome atualizado do capitão", "phone": "(16) 99999-9999"}
    path = f"/api/admin/students/{captain.id}/profile"
    as_user(client, captain)
    assert client.put(path, json=body).status_code == 403
    as_user(client, world.admin)
    response = client.put(path, json=body)
    assert response.status_code == 200 and response.json()["id"] == str(captain.id)
    with world.db() as db:
        row = db.get(User, captain.id)
        assert row.name == body["name"] and row.phone == body["phone"]
        assert row.is_captain and row.login == captain.login
