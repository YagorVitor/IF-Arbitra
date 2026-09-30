from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.commands.verify_run import verify
from app.db.models import AllocationAdjustment, AuditEvent
from tests.support import as_user, draft_payload, register

pytestmark = pytest.mark.integration


def process_trios(world, client, monkeypatch, count):
    as_user(client, world.admin)
    response = client.post("/api/admin/rounds", json=draft_payload(world))
    assert response.status_code == 201, response.text
    rid = response.json()["id"]
    assert (
        client.post(f"/api/admin/rounds/{rid}/transition", json={"action": "open"}).status_code
        == 200
    )
    groups = []
    for index in range(count):
        response = register(client, world, range(index * 3, index * 3 + 3), round_id=rid)
        assert response.status_code == 201, response.text
        group = response.json()
        groups.append(group)
        # First-choice competition, different rankings, and one unranked trio.
        if index != count - 1:
            order = (
                world.staff if index % 3 != 1 else [world.staff[1], world.staff[0], world.staff[2]]
            )
            response = client.put(
                f"/api/sextets/{group['id']}/preferences",
                json={"staff_ids": [str(s.id) for s in order], "expected_version": 0},
            )
            assert response.status_code == 200, response.text
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    as_user(client, world.admin)
    response = client.post(f"/api/admin/rounds/{rid}/allocate")
    assert response.status_code == 200, response.text
    return rid, groups, response.json()["id"]


def payload(results):
    return {
        "expected_revision": results["revision"],
        "reason": "Ajuste administrativo para organizar os trios de teste.",
        "assignments": [
            {"allocation_id": a["id"], "staff_id": a["staff_id"]} for a in results["allocations"]
        ],
    }


def test_single_pending_trio_can_be_assigned_and_student_sees_updated_result(
    world, client, monkeypatch
):
    rid, groups, run_id = process_trios(world, client, monkeypatch, 5)
    results = client.get(f"/api/rounds/{rid}/results").json()
    pending = [a for a in results["allocations"] if a["status"] == "UNALLOCATED"]
    assert len(pending) == 1
    free_staff = next(
        str(s.id)
        for s in world.staff
        if str(s.id) not in {a["staff_id"] for a in results["allocations"]}
    )
    data = payload(results)
    next(a for a in data["assignments"] if a["allocation_id"] == pending[0]["id"])["staff_id"] = (
        free_staff
    )
    path = f"/api/admin/rounds/{rid}/assignments"
    as_user(client, world.users[0])
    assert client.put(path, json=data).status_code == 403
    assert client.get(f"/api/rounds/{rid}/results").json()["allocations"] == []
    as_user(client, world.admin)
    response = client.put(path, json=data)
    assert response.status_code == 200, response.text
    assert response.json()["revision"] == 1
    assert client.put(path, json=data).json()["code"] == "ADJUSTMENT_CONFLICT"
    assert client.get(f"/api/rounds/{rid}").json()["pending"] == 0
    with world.db() as db:
        assert verify(db, UUID(run_id)) == 5
        assert db.scalar(select(AllocationAdjustment)).reason == data["reason"]
        audit = db.scalar(
            select(AuditEvent).where(AuditEvent.entity_type == "ALLOCATION_ADJUSTMENT")
        )
        assert audit.previous_state[pending[0]["id"]] is None
    assert (
        client.post(f"/api/admin/rounds/{rid}/transition", json={"action": "publish"}).status_code
        == 200
    )
    target = next(g for g in groups if g["id"] == pending[0]["sextet_id"])
    member = next(u for u in world.users if str(u.id) == target["members"][0]["id"])
    as_user(client, member)
    result = client.get(f"/api/rounds/{rid}/results").json()
    assert result["published"]
    assert len(result["allocations"]) == 1
    assert result["adjustment_reason"] is None
    allocation = result["allocations"][0]
    assert allocation["staff_id"] == free_staff
    assert allocation["manually_adjusted"]
    assert allocation["partner_trio"] is None
    assert allocation["trace"]["chosen"] == free_staff
    as_user(client, world.admin)
    assert (
        client.post(f"/api/admin/rounds/{rid}/transition", json={"action": "archive"}).status_code
        == 200
    )
    data["expected_revision"] = 1
    assert client.put(path, json=data).json()["code"] == "ADJUSTMENT_NOT_ALLOWED"


def test_eight_trios_capacity_validation_and_repair_published_pair(world, client, monkeypatch):
    rid, groups, run_id = process_trios(world, client, monkeypatch, 8)
    results = client.get(f"/api/rounds/{rid}/results").json()
    assert len(results["allocations"]) == 8
    pending = [a for a in results["allocations"] if a["staff_id"] is None]
    assert len(pending) == 2
    allocated = next(a for a in results["allocations"] if a["staff_id"])
    data = payload(results)
    path = f"/api/admin/rounds/{rid}/assignments"
    for item in data["assignments"]:
        if item["allocation_id"] == pending[0]["id"]:
            item["staff_id"] = allocated["staff_id"]
    assert client.put(path, json=data).json()["code"] == "STAFF_CAPACITY_EXCEEDED"
    assert client.get(f"/api/rounds/{rid}/results").json()["revision"] == 0
    assert (
        client.post(f"/api/admin/rounds/{rid}/transition", json={"action": "publish"}).status_code
        == 200
    )
    # Swap a complete pair for the two pending trios, leaving the previous pair pending.
    for item in data["assignments"]:
        original = next(a for a in results["allocations"] if a["id"] == item["allocation_id"])
        if original["staff_id"] == allocated["staff_id"]:
            item["staff_id"] = None
        elif original["staff_id"] is None:
            item["staff_id"] = allocated["staff_id"]
    response = client.put(path, json=data)
    assert response.status_code == 200, response.text
    adjusted = client.get(f"/api/rounds/{rid}/results").json()
    repaired = [a for a in adjusted["allocations"] if a["id"] in {p["id"] for p in pending}]
    assert {a["staff_slot"] for a in repaired} == {1, 2}
    assert all(a["partner_trio"]["id"] in {p["sextet_id"] for p in pending} for a in repaired)
    assert client.get(f"/api/rounds/{rid}").json()["pending"] == 2
    with world.db() as db:
        assert verify(db, UUID(run_id)) == 8
    with pytest.raises(IntegrityError), world.db.begin() as db:
        db.execute(
            text("UPDATE allocation_adjustments SET reason = 'tampered' WHERE round_id = :id"),
            {"id": rid},
        )
    # A foreign round allocation or duplicated entry cannot enter the revision.
    data = payload(adjusted)
    data["assignments"][0]["allocation_id"] = data["assignments"][1]["allocation_id"]
    assert client.put(path, json=data).json()["code"] == "INVALID_ASSIGNMENTS"


def test_adjustment_before_processing_is_rejected(world, client):
    as_user(client, world.admin)
    assert (
        client.put(
            f"/api/admin/rounds/{world.round.id}/assignments",
            json={
                "expected_revision": 0,
                "reason": "Ainda não processada.",
                "assignments": [{"allocation_id": str(world.users[0].id), "staff_id": None}],
            },
        ).json()["code"]
        == "ADJUSTMENT_NOT_ALLOWED"
    )
