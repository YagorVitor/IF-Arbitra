from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    AllocationRun,
    SextetMember,
)
from tests.support import as_user, draft_payload, register

pytestmark = pytest.mark.integration


def test_round_lifecycle_and_staff_before_after(world, client):
    as_user(client, world.admin)
    data = draft_payload(world)
    response = client.post("/api/admin/rounds", json=data)
    assert response.status_code == 201, response.text
    rid = response.json()["id"]
    as_user(client, world.users[0])
    assert rid not in [r["id"] for r in client.get("/api/rounds").json()]
    assert client.get(f"/api/rounds/{rid}").status_code == 404
    assert client.get(f"/api/rounds/{rid}/results").status_code == 404
    as_user(client, world.admin)
    data["staff_ids"].reverse()
    assert client.put(f"/api/admin/rounds/{rid}", json=data).status_code == 200
    event = client.get("/api/admin/audit", params={"entity": rid}).json()["events"][0]
    assert event["previous_state"]["staff_ids"] == [str(s.id) for s in world.staff]
    assert event["resulting_state"]["staff_ids"] == data["staff_ids"]
    path = f"/api/admin/rounds/{rid}/transition"
    assert client.post(path, json={"action": "publish"}).status_code == 409
    staff = world.staff[0]
    staff_path = f"/api/admin/staff/{staff.id}"
    assert client.put(staff_path, json={"name": "Servidor A", "active": False}).status_code == 200
    response = client.post(path, json={"action": "open"})
    assert response.status_code == 422
    assert response.json()["code"] == "STAFF_NOT_ELIGIBLE"
    assert client.put(staff_path, json={"name": "Servidor A", "active": True}).status_code == 200
    assert client.post(path, json={"action": "open"}).status_code == 200
    assert client.post(path, json={"action": "open"}).status_code == 200
    assert client.put(f"/api/admin/rounds/{rid}", json=data).status_code == 409


def test_archiving_releases_members_and_run_evidence_is_immutable(world, client, monkeypatch):
    first = register(client, world).json()
    as_user(client, world.admin)
    monkeypatch.setattr(
        "app.services.allocation.database_now", lambda db: world.round.preferences_close_at
    )
    result = client.post(f"/api/admin/rounds/{world.round.id}/allocate")
    assert result.status_code == 200, result.text
    run_id = UUID(result.json()["id"])
    from app.commands.verify_run import verify

    with world.db() as db:
        assert verify(db, run_id) == 1
        run = db.get(AllocationRun, run_id)
        run.input_fingerprint = "0" * 64
        with db.no_autoflush, pytest.raises(ValueError, match="impressão digital"):
            verify(db, run_id)
        db.rollback()
    with pytest.raises(IntegrityError), world.db.begin() as db:
        db.get(AllocationRun, run_id).snapshot = {"tampered": True}
    path = f"/api/admin/rounds/{world.round.id}/transition"
    assert client.post(path, json={"action": "publish"}).status_code == 200
    assert client.post(path, json={"action": "archive"}).status_code == 200
    with world.db() as db:
        assert (
            db.scalar(select(func.count()).select_from(SextetMember).where(SextetMember.active))
            == 0
        )
    new = client.post("/api/admin/rounds", json=draft_payload(world)).json()
    assert (
        client.post(
            f"/api/admin/rounds/{new['id']}/transition", json={"action": "open"}
        ).status_code
        == 200
    )
    as_user(client, world.users[0])
    response = client.post(
        f"/api/rounds/{new['id']}/sextets",
        json={
            "name": "Novo grupo",
            "members": [str(u.id) for u in world.users[:6]],
            "idempotency_key": str(uuid4()),
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["id"] != first["id"]
    assert len(client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"]) == 1
