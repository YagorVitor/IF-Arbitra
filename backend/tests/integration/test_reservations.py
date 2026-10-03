from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.commands.verify_run import verify
from app.db.models import AllocationRound, AuditEvent, RoundStaff, StaffReservation, User
from tests.support import as_user

pytestmark = pytest.mark.integration


def prepare(world, excluded_staff=None):
    with world.db.begin() as db:
        round_ = AllocationRound(
            name="Rodada de reservas",
            formation_mode="GROUPS",
            registration_opens_at=world.round.registration_opens_at,
            registration_closes_at=world.round.registration_closes_at,
            preferences_open_at=world.round.preferences_open_at,
            preferences_close_at=world.round.preferences_close_at,
        )
        db.add(round_)
        db.flush()
        db.add_all(
            [
                RoundStaff(round_id=round_.id, staff_id=s.id, order=i)
                for i, s in enumerate(world.staff)
                if s.id != excluded_staff
            ]
        )
        db.flush()
        round_.status = "OPEN"
        world.round = round_
        for index, user in enumerate(world.users):
            db.get(User, user.id).is_captain = index in {0, 6, 12}


def reservation(client, world, captain=6, staff=0):
    return client.put(
        f"/api/admin/students/{world.users[captain].id}/reservation",
        json={
            "staff_id": str(world.staff[staff].id) if staff is not None else None,
            "reason": "Reserva autorizada para acompanhamento do grupo.",
        },
    )


def group(client, world, start):
    as_user(client, world.users[start])
    response = client.post(
        f"/api/rounds/{world.round.id}/sextets",
        json={
            "name": f"Grupo {start}",
            "members": [str(u.id) for u in world.users[start : start + 6]],
            "idempotency_key": str(uuid4()),
        },
    )
    assert response.status_code == 201, response.text
    gid = response.json()["id"]
    assert (
        client.put(
            f"/api/sextets/{gid}/preferences",
            json={
                "staff_ids": [
                    s["id"] for s in client.get(f"/api/rounds/{world.round.id}").json()["staff"]
                ],
                "expected_version": 0,
            },
        ).status_code
        == 200
    )
    return gid


def test_admin_reservation_privacy_capacity_snapshot_and_removal(world, client, monkeypatch):
    prepare(world)
    as_user(client, world.admin)
    assert reservation(client, world).status_code == 204
    assert reservation(client, world, captain=0).status_code == 409
    assert reservation(client, world, captain=1, staff=1).status_code == 422
    rows = client.get("/api/admin/reservations").json()
    assert rows[0]["captain_id"] == str(world.users[6].id)
    assert rows[0]["enabled"]
    first, reserved = group(client, world, 0), group(client, world, 6)
    assert client.get("/api/admin/reservations").status_code == 403
    assert reservation(client, world, staff=1).status_code == 403
    assert "reservations" not in client.get(f"/api/rounds/{world.round.id}").json()
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    as_user(client, world.admin)
    run = client.post(f"/api/admin/rounds/{world.round.id}/allocate")
    assert run.status_code == 200, run.text
    result = {
        a["sextet_id"]: a
        for a in client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"]
    }
    assert result[reserved]["staff_id"] == str(world.staff[0].id)
    assert result[first]["staff_id"] == str(world.staff[1].id)
    assert result[reserved]["manually_adjusted"]
    assert result[reserved]["preference_position"] is None
    frozen = client.get(f"/api/admin/runs/{run.json()['id']}").json()["snapshot"]
    assert frozen["reservations"][0]["reason"].startswith("Reserva autorizada")
    assert (
        client.post(
            f"/api/admin/rounds/{world.round.id}/transition", json={"action": "publish"}
        ).status_code
        == 200
    )
    as_user(client, world.users[0])
    student = client.get(f"/api/rounds/{world.round.id}/results").json()
    assert len(student["allocations"]) == 1 and student["allocations"][0]["sextet_id"] == first
    assert "Reserva autorizada" not in str(student)
    assert client.get(f"/api/admin/runs/{run.json()['id']}").status_code == 403
    as_user(client, world.admin)
    assert reservation(client, world, staff=None).status_code == 204
    assert client.get("/api/admin/reservations").json() == []
    with world.db() as db:
        assert verify(db, UUID(run.json()["id"])) == 2
        assert not db.scalar(
            select(AuditEvent).where(AuditEvent.entity_type == "STAFF_RESERVATION")
        )


def test_no_group_releases_staff_and_reservation_persists(world, client, monkeypatch):
    prepare(world)
    as_user(client, world.admin)
    assert reservation(client, world).status_code == 204
    gid = group(client, world, 0)
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    as_user(client, world.admin)
    run = client.post(f"/api/admin/rounds/{world.round.id}/allocate")
    assert run.status_code == 200
    result = client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"]
    assert result[0]["sextet_id"] == gid and result[0]["staff_id"] == str(world.staff[0].id)
    assert not result[0]["manually_adjusted"]
    assert len(client.get("/api/admin/reservations").json()) == 1
    with world.db() as db:
        assert db.get(StaffReservation, world.users[6].id)
        assert verify(db, UUID(run.json()["id"])) == 1


def test_missing_reserved_staff_blocks_processing_without_fallback(world, client, monkeypatch):
    prepare(world, excluded_staff=world.staff[0].id)
    as_user(client, world.admin)
    assert reservation(client, world).status_code == 204
    group(client, world, 6)
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    as_user(client, world.admin)
    response = client.post(f"/api/admin/rounds/{world.round.id}/allocate")
    assert response.status_code == 409
    assert response.json()["code"] == "RESERVED_STAFF_NOT_ELIGIBLE"
    assert client.get(f"/api/rounds/{world.round.id}/results").json()["allocations"] == []
