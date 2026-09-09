import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from conftest import as_user, register
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.models import (
    Allocation,
    AllocationRun,
    AuditEvent,
    InstitutionalStaff,
    Sextet,
    SextetMember,
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


def test_seed_idempotent_and_names_preserved(world):
    from app.seed import STAFF, seed

    seed()
    with world.db.begin() as db:
        db.get(InstitutionalStaff, UUID(STAFF[0][0])).name = "Nome corrigido"
    seed()
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(InstitutionalStaff)) == 17
        assert db.get(InstitutionalStaff, UUID(STAFF[0][0])).name == "Nome corrigido"


def test_composition_authority_idempotency_and_constraints(world, client):
    key = uuid4()
    response = register(client, world, key=key)
    assert response.status_code == 201, response.text
    first = response.json()
    assert len(first["members"]) == 6
    assert register(client, world, key=key).json() == first
    changed = register(client, world, indices=[0, 1, 2, 3, 4, 6], key=key)
    assert changed.status_code == 409
    as_user(client, world.users[6])
    assert client.get(f"/api/sextets/{first['id']}").status_code == 404
    as_user(client, world.users[3])
    assert (
        client.put(
            f"/api/sextets/{first['id']}/preferences",
            json={"staff_ids": [str(s.id) for s in world.staff], "expected_version": 0},
        ).status_code
        == 403
    )
    with pytest.raises(IntegrityError), world.db.begin() as db:
        db.execute(
            text("UPDATE sextets SET registration_completed_at = now() WHERE id=:id"),
            {"id": first["id"]},
        )
    with pytest.raises(IntegrityError), world.db.begin() as db:
        db.add(
            Sextet(
                round_id=world.round.id,
                created_by=world.users[6].id,
                name="Incompleto",
                idempotency_key=uuid4(),
            )
        )
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(Sextet)) == 1
        assert db.scalar(select(func.count()).select_from(SextetMember)) == 6


@pytest.mark.parametrize("indices", [[0, 0, 1, 2, 3, 4], [0, 1, 2, 3, 4]])
def test_invalid_composition(world, client, indices):
    assert register(client, world, indices=indices).status_code == 422
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(Sextet)) == 0


def test_concurrent_student_overlap(world):
    import threading

    barrier = threading.Barrier(2)

    def submit(indices):
        with TestClient(app, headers={"Origin": "http://localhost:5173"}) as client:
            barrier.wait()
            return register(client, world, indices).status_code

    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(submit, [range(6), [6, 7, 8, 9, 10, 5]]))
    assert sorted(responses) == [201, 409]
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(Sextet)) == 1
        assert db.scalar(select(func.count()).select_from(SextetMember)) == 6


def test_burst_50_requests(world):
    import threading

    barrier = threading.Barrier(50)

    def submit(_):
        with TestClient(app, headers={"Origin": "http://localhost:5173"}) as client:
            barrier.wait()
            started = time.perf_counter()
            status = register(client, world).status_code
            return status, (time.perf_counter() - started) * 1000

    with ThreadPoolExecutor(50) as pool:
        responses = list(pool.map(submit, range(50)))
    codes = [r[0] for r in responses]
    assert codes.count(201) == 1 and codes.count(409) == 49, codes
    durations = sorted(r[1] for r in responses)
    print(
        f"BURST 50: 1 success, 49 conflicts, 0 internal errors; p50={durations[24]:.0f}ms p95={durations[47]:.0f}ms max={durations[-1]:.0f}ms"
    )
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(SextetMember)) == 6


def test_ranking_validation_version_deadline_and_priority(world, client, monkeypatch):
    first = register(client, world).json()
    path = f"/api/sextets/{first['id']}/preferences"
    ids = [str(s.id) for s in world.staff]
    for ranking in [ids[:2], [ids[0]] * 3, [*ids[:2], str(uuid4())]]:
        assert (
            client.put(path, json={"staff_ids": ranking, "expected_version": 0}).status_code == 422
        )
    assert client.put(path, json={"staff_ids": ids, "expected_version": 0}).status_code == 200
    assert client.put(path, json={"staff_ids": ids, "expected_version": 0}).json()["version"] == 1
    assert client.put(path, json={"staff_ids": ids[::-1], "expected_version": 0}).status_code == 409
    assert client.put(path, json={"staff_ids": ids[::-1], "expected_version": 1}).status_code == 200
    assert (
        client.get(f"/api/sextets/{first['id']}").json()["registration_completed_at"]
        == first["registration_completed_at"]
    )
    monkeypatch.setattr("app.services.database_now", lambda db: world.round.preferences_close_at)
    assert client.put(path, json={"staff_ids": ids, "expected_version": 2}).status_code == 409
    with world.db() as db:
        assert db.scalar(
            select(AuditEvent).where(
                AuditEvent.event_type == "OPERATION_REJECTED",
                AuditEvent.payload["code"].astext == "PREFERENCE_WINDOW_CLOSED",
            )
        )


def prepare_groups(world, client):
    groups = []
    for indices, ranking in [
        (range(6), world.staff),
        (range(6, 12), [world.staff[0], world.staff[2], world.staff[1]]),
        (range(12, 18), None),
        (range(18, 24), None),
    ]:
        response = register(client, world, indices)
        assert response.status_code == 201, response.text
        s = response.json()
        groups.append(s)
        if ranking:
            assert (
                client.put(
                    f"/api/sextets/{s['id']}/preferences",
                    json={"staff_ids": [str(i.id) for i in ranking], "expected_version": 0},
                ).status_code
                == 200
            )
    return groups


def test_allocation_concurrent_idempotent_publication_and_dispute(world, client, monkeypatch):
    groups = prepare_groups(world, client)
    monkeypatch.setattr(
        "app.services.database_now",
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
    monkeypatch.setattr("app.services.database_now", lambda db: world.round.preferences_close_at)
    from app.allocation import allocate

    def broken(*args):
        yield allocate(*args)[0]
        raise RuntimeError("injected failure")

    monkeypatch.setattr("app.services.allocate", broken)
    as_user(client, world.admin)
    path = f"/api/admin/rounds/{world.round.id}/allocate"
    assert client.post(path).status_code == 500
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(Allocation)) == 0
        assert list(db.scalars(select(AllocationRun.status))) == ["FAILED"]
        assert db.scalar(select(AuditEvent).where(AuditEvent.event_type == "ALLOCATION_FAILED"))
    monkeypatch.setattr("app.services.allocate", allocate)
    assert client.post(path).status_code == 200


def test_audit_append_only_and_ready(world, client):
    register(client, world)
    assert client.get("/ready").status_code == 200
    for sql in [
        "DELETE FROM audit_events",
        "UPDATE audit_events SET payload='{}'::jsonb",
        "TRUNCATE audit_events",
    ]:
        with pytest.raises(IntegrityError), world.db.begin() as db:
            db.execute(text(sql))
