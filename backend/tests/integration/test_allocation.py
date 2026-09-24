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
from tests.support import as_user, prepare_groups, register

pytestmark = pytest.mark.integration


def test_smaller_groups_rank_and_receive_staff(world, client, monkeypatch):
    groups = [
        register(client, world, indices=range(3)),
        register(client, world, indices=range(3, 8)),
        register(client, world, indices=range(8, 14)),
    ]
    assert all(group.status_code == 201 for group in groups), [g.text for g in groups]
    for group, leader in zip(groups, [world.users[i] for i in (0, 3, 8)], strict=True):
        group = group.json()
        as_user(client, leader)
        response = client.put(
            f"/api/sextets/{group['id']}/preferences",
            json={"staff_ids": [str(s.id) for s in world.staff], "expected_version": 0},
        )
        assert response.status_code == 200, response.text
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    as_user(client, world.admin)
    run = client.post(f"/api/admin/rounds/{world.round.id}/allocate")
    assert run.status_code == 200
    assert [
        g["member_count"]
        for g in client.get(f"/api/admin/runs/{run.json()['id']}").json()["snapshot"]["groups"]
    ] == [3, 5, 6]
    allocations = client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"]
    assert [item["sextet_id"] for item in allocations] == [g.json()["id"] for g in groups]
    assert [item["staff_id"] for item in allocations] == [str(s.id) for s in world.staff]


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
