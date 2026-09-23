from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import (
    Allocation,
    AllocationRun,
    AuditEvent,
)
from app.main import app
from tests.support import as_user, prepare_groups

pytestmark = pytest.mark.integration


def test_allocation_concurrent_idempotent_publication_and_dispute(world, client, monkeypatch):
    groups = prepare_groups(world, client)
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )

    def run(_):
        with TestClient(app, headers={"Origin": "http://localhost:5173"}) as c:
            as_user(c, world.admin)
            return c.post(f"/api/admin/rounds/{world.round.id}/allocate")

    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(run, range(2)))
    assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
    assert responses[0].json()["id"] == responses[1].json()["id"]
    as_user(client, world.users[0])
    assert client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"] == []
    as_user(client, world.admin)
    result = client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"]
    assert [a["staff_name"] for a in result] == ["A", "C", "B", None]
    assert result[-1]["status"] == "UNALLOCATED"
    trace = result[1]["trace"]
    assert trace["unavailable"] == [
        {"staff_id": str(world.staff[0].id), "sextet_id": groups[0]["id"]}
    ]
    run = client.get(f"/api/admin/runs/{responses[0].json()['id']}").json()
    assert run["snapshot"]["groups"][1]["preferences"][1] == str(world.staff[2].id)
    assert (
        client.post(
            f"/api/admin/rounds/{world.round.id}/transition", json={"action": "publish"}
        ).status_code
        == 200
    )
    as_user(client, world.users[6])
    assert len(client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"]) == 1
    assert client.get("/api/admin/audit").status_code == 403


def test_failed_allocation_rolls_back_and_can_retry(world, client, monkeypatch):
    prepare_groups(world, client)
    monkeypatch.setattr(
        "app.services.allocation.database_now", lambda db: world.round.preferences_close_at
    )
    from app.domain.allocation import allocate

    def broken(*args):
        yield allocate(*args)[0]
        raise RuntimeError("injected failure")

    monkeypatch.setattr("app.services.allocation.allocate", broken)
    as_user(client, world.admin)
    path = f"/api/admin/rounds/{world.round.id}/allocate"
    assert client.post(path).status_code == 500
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(Allocation)) == 0
        assert list(db.scalars(select(AllocationRun.status))) == ["FAILED"]
        assert db.scalar(select(AuditEvent).where(AuditEvent.event_type == "ALLOCATION_FAILED"))
    monkeypatch.setattr("app.services.allocation.allocate", allocate)
    assert client.post(path).status_code == 200
