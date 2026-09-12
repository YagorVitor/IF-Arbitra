import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    AllocationRound,
    RoundStaff,
    Sextet,
    SextetMember,
)
from app.main import app
from tests.support import as_user, register

pytestmark = pytest.mark.integration


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


def test_literal_backslash_student_search(world, client):
    as_user(client, world.users[0])
    response = client.get("/api/students", params={"q": "x\\"})
    assert response.status_code == 200
    assert response.json() == []


def test_registration_exact_deadline(world, client, monkeypatch):
    monkeypatch.setattr(
        "app.services.rounds.database_now", lambda db: world.round.registration_closes_at
    )
    response = register(client, world)
    assert response.status_code == 409
    assert response.json()["code"] == "REGISTRATION_WINDOW_CLOSED"
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(Sextet)) == 0


def test_different_rounds_still_enforce_student_exclusivity(world):
    from fastapi.testclient import TestClient

    from app.main import app

    with world.db.begin() as db:
        other = AllocationRound(
            **{
                k: getattr(world.round, k)
                for k in (
                    "name",
                    "registration_opens_at",
                    "registration_closes_at",
                    "preferences_open_at",
                    "preferences_close_at",
                )
            }
        )
        db.add(other)
        db.flush()
        db.add_all(
            RoundStaff(round_id=other.id, staff_id=s.id, order=i) for i, s in enumerate(world.staff)
        )
        db.flush()
        other.status = "OPEN"

    import threading

    barrier = threading.Barrier(2)

    def submit(values):
        rid, indices = values
        with TestClient(app, headers={"Origin": "http://localhost:5173"}) as c:
            as_user(c, world.users[indices[0]])
            barrier.wait(timeout=10)
            return c.post(
                f"/api/rounds/{rid}/sextets",
                json={
                    "name": "Concorrente",
                    "members": [str(world.users[i].id) for i in indices],
                    "idempotency_key": str(uuid4()),
                },
            ).status_code

    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(submit, [(world.round.id, list(range(6))), (other.id, [6, 7, 8, 9, 10, 5])])
        )
    assert sorted(results) == [201, 409]
    with world.db() as db:
        assert db.scalar(select(func.count()).select_from(SextetMember)) == 6
