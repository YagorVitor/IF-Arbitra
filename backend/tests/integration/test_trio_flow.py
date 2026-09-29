from datetime import timedelta
from uuid import UUID

import pytest

from tests.support import as_user, draft_payload, register

pytestmark = pytest.mark.integration


def test_trios_form_pairs_by_preference_and_pending_remains_visible(world, client, monkeypatch):
    as_user(client, world.admin)
    payload = {**draft_payload(world), "name": "Rodada de trios", "formation_mode": "TRIOS"}
    created = client.post("/api/admin/rounds", json=payload)
    assert created.status_code == 201, created.text
    round_id = created.json()["id"]
    assert created.json()["capacity"] == 6
    assert (
        client.post(f"/api/admin/rounds/{round_id}/transition", json={"action": "open"}).status_code
        == 200
    )

    invalid = register(client, world, range(4), round_id=round_id)
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "INVALID_TRIO_COMPOSITION"

    groups = []
    for start in (0, 3, 6, 9, 12):
        response = register(client, world, range(start, start + 3), round_id=round_id)
        assert response.status_code == 201, response.text
        group = response.json()
        assert group["member_count"] == 3
        groups.append(group)
        if start != 12:
            saved = client.put(
                f"/api/sextets/{group['id']}/preferences",
                json={
                    "staff_ids": [str(staff.id) for staff in world.staff],
                    "expected_version": 0,
                },
            )
            assert saved.status_code == 200, saved.text

    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    as_user(client, world.admin)
    processed = client.post(f"/api/admin/rounds/{round_id}/allocate")
    assert processed.status_code == 200, processed.text
    allocations = client.get(f"/api/rounds/{round_id}/results").json()["allocations"]
    by_trio = {allocation["sextet_id"]: allocation for allocation in allocations}
    assert [by_trio[group["id"]]["staff_name"] for group in groups] == ["A", "A", "B", "B", None]
    assert by_trio[groups[0]["id"]]["partner_trio"]["id"] == groups[1]["id"]
    assert len(by_trio[groups[0]["id"]]["partner_trio"]["members"]) == 3
    assert by_trio[groups[-1]["id"]]["status"] == "UNALLOCATED"
    assert by_trio[groups[-1]["id"]]["trace"]["reason"] == "AWAITING_PAIR"

    from app.commands.verify_run import verify
    from app.db.models import AllocationRun

    with world.db() as db:
        run = db.get(AllocationRun, UUID(processed.json()["id"]))
        assert run.algorithm_version == "trio-preference-pairs-v1"
        assert verify(db, run.id) == 5

    assert (
        client.post(
            f"/api/admin/rounds/{round_id}/transition", json={"action": "publish"}
        ).status_code
        == 200
    )
    as_user(client, world.users[0])
    student_result = client.get(f"/api/rounds/{round_id}/results").json()
    assert len(student_result["allocations"]) == 1
    assert student_result["allocations"][0]["partner_trio"]["id"] == groups[1]["id"]
