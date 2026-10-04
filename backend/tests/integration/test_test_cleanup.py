from datetime import timedelta

import pytest
from pydantic import SecretStr
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.db.models import AuditEvent, User
from tests.support import as_user, prepare_groups

pytestmark = pytest.mark.integration


def test_cleanup_removes_archived_test_data_preserves_real_access_and_restores_guards(
    world, client, monkeypatch
):
    with world.db.begin() as db:
        db.add(User(name="QA descartável", login="qa-aluno-99@if-arbitra.invalid", active=False))
    prepare_groups(world, client)
    as_user(client, world.admin)
    assert client.get("/api/admin/maintenance/test-data").status_code == 409
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    assert client.post(f"/api/admin/rounds/{world.round.id}/allocate").status_code == 200
    assert (
        client.post(
            f"/api/admin/rounds/{world.round.id}/transition", json={"action": "publish"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/admin/rounds/{world.round.id}/transition", json={"action": "archive"}
        ).status_code
        == 200
    )
    preview = client.get("/api/admin/maintenance/test-data").json()
    assert preview["counts"]["users"] == 1 and preview["counts"]["rounds"] == 1
    assert "password_hash" not in str(preview)
    as_user(client, world.users[0])
    assert client.get("/api/admin/maintenance/test-data").status_code == 403
    assert (
        client.post(
            "/api/admin/maintenance/test-data/cleanup",
            json={"fingerprint": preview["fingerprint"], "confirm_test_data": True},
        ).status_code
        == 403
    )
    as_user(client, world.admin)
    bad = client.post(
        "/api/admin/maintenance/test-data/cleanup",
        json={"fingerprint": "0" * 64, "confirm_test_data": True},
    )
    assert bad.status_code == 409
    preview = client.get("/api/admin/maintenance/test-data").json()
    with world.db() as db:
        old_hash = db.get(User, world.admin.id).password_hash
    response = client.post(
        "/api/admin/maintenance/test-data/cleanup",
        json={"fingerprint": preview["fingerprint"], "confirm_test_data": True},
    )
    assert response.status_code == 200, response.text
    assert client.get("/api/rounds").json() == []
    assert client.get("/api/admin/maintenance/test-data").status_code == 409
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 91
        assert db.get(User, world.admin.id).password_hash == old_hash
        assert db.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert (
            db.scalar(
                text("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgenabled = 'D'")
            )
            == 0
        )
    with pytest.raises(IntegrityError), world.db.begin() as db:
        db.execute(text("DELETE FROM audit_events"))


def test_test_email_only_targets_admin_and_does_not_issue_credentials(world, client, monkeypatch):
    sent = []
    monkeypatch.setattr("app.services.credential_dispatch._send_message", sent.append)
    from app.core.config import settings

    monkeypatch.setattr(settings(), "smtp_host", "smtp.example.org")
    monkeypatch.setattr(settings(), "smtp_from", "IF-Arbitra <test@example.org>")
    with world.db.begin() as db:
        db.get(User, world.admin.id).email = "admin@example.org"
        before = {str(u.id): u.password_hash for u in db.scalars(select(User))}
    as_user(client, world.users[0])
    assert client.post("/api/admin/email/test").status_code == 403
    as_user(client, world.admin)
    response = client.post("/api/admin/email/test")
    assert response.status_code == 200, response.text
    assert response.json()["recipient"] == "admin@example.org"
    assert len(sent) == 1 and sent[0]["To"] == "admin@example.org"
    assert sent[0]["Subject"].startswith("[TESTE]")
    assert "SENHA-DE-TESTE" in sent[0].get_body(preferencelist=("plain",)).get_content()
    with world.db() as db:
        assert {str(u.id): u.password_hash for u in db.scalars(select(User))} == before


def test_test_email_uses_resend_and_sends_only_to_admin(world, client, monkeypatch):
    from app.core.config import settings

    calls = []

    class Response:
        def raise_for_status(self):
            return None

    monkeypatch.setattr(settings(), "resend_api_key", SecretStr("re_test_secret"))
    monkeypatch.setattr(settings(), "resend_from", "IF-Arbitra <onboarding@resend.dev>")
    monkeypatch.setattr(
        "app.services.credential_dispatch.httpx.post",
        lambda *args, **kwargs: calls.append((args, kwargs)) or Response(),
    )
    with world.db.begin() as db:
        db.get(User, world.admin.id).email = "admin@example.org"

    as_user(client, world.admin)
    response = client.post("/api/admin/email/test")

    assert response.status_code == 200, response.text
    assert response.json()["recipient"] == "admin@example.org"
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[0] == "https://api.resend.com/emails"
    assert kwargs["headers"]["Authorization"] == "Bearer re_test_secret"
    assert kwargs["json"]["from"] == "IF-Arbitra <onboarding@resend.dev>"
    assert kwargs["json"]["to"] == ["admin@example.org"]
    assert kwargs["json"]["subject"].startswith("[TESTE]")
    assert "SENHA-DE-TESTE" in kwargs["json"]["text"]
