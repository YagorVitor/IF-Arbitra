from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from app.commands.verify_run import verify
from app.db.models import InstitutionalStaff
from tests.support import as_user, draft_payload

pytestmark = pytest.mark.integration


def test_full_74_student_round_enforces_sizes_captain_quotas_and_unique_servers(
    world, client, monkeypatch
):
    with world.db.begin() as db:
        extra = [InstitutionalStaff(name=f"Servidor extra {i}") for i in range(8)]
        db.add_all(extra)
    with world.db.begin() as db:
        from app.db.models import User

        captains = {0, 7, 14, 21, 28, 35, 42, 49, 56, 62, 68, 74}
        for index, student in enumerate(world.users):
            db.get(User, student.id).is_captain = index in captains
    staff = [*world.staff, *extra]
    as_user(client, world.admin)
    created = client.post(
        "/api/admin/rounds",
        json={
            **draft_payload(world),
            "formation_mode": "GROUPS",
            "staff_ids": [str(s.id) for s in staff],
        },
    )
    assert created.status_code == 201, created.text
    rid = created.json()["id"]
    assert created.json()["limit_six"] == 3 and created.json()["limit_seven"] == 8
    assert created.json()["capacity"] == 11
    assert (
        client.post(f"/api/admin/rounds/{rid}/transition", json={"action": "open"}).status_code
        == 200
    )
    offset = 0
    groups = []
    for size in [7] * 8 + [6] * 3:
        members = world.users[offset : offset + size]
        as_user(client, members[0])
        body = {
            "name": f"Grupo {len(groups) + 1}",
            "members": [str(u.id) for u in members],
            "idempotency_key": str(uuid4()),
        }
        if offset == 0:
            invalid = client.post(
                f"/api/rounds/{rid}/sextets", json={**body, "members": body["members"][:5]}
            )
            assert (
                invalid.status_code == 422 and invalid.json()["code"] == "INVALID_GROUP_COMPOSITION"
            )
            wrong_captain = client.post(
                f"/api/rounds/{rid}/sextets",
                json={**body, "members": body["members"][1:] + body["members"][:1]},
            )
            assert wrong_captain.status_code == 403
        response = client.post(f"/api/rounds/{rid}/sextets", json=body)
        assert response.status_code == 201, response.text
        group = response.json()
        assert group["leader_id"] == str(members[0].id)
        assert len(group["members"]) == size
        assert group["members"][-1]["slot"] == size - 1
        assert client.post(f"/api/rounds/{rid}/sextets", json=body).json()["id"] == group["id"]
        ranking = {"staff_ids": [str(s.id) for s in staff], "expected_version": 0}
        as_user(client, members[1])
        assert (
            client.put(f"/api/sextets/{group['id']}/preferences", json=ranking).status_code == 403
        )
        as_user(client, members[0])
        if len(groups) < 10:
            assert (
                client.put(f"/api/sextets/{group['id']}/preferences", json=ranking).status_code
                == 200
            )
        groups.append(group)
        offset += size
    assert offset == 74
    for size in (6, 7):
        as_user(client, world.users[74])
        response = client.post(
            f"/api/rounds/{rid}/sextets",
            json={
                "name": "Excedente",
                "members": [str(u.id) for u in world.users[74 : 74 + size]],
                "idempotency_key": str(uuid4()),
            },
        )
        assert response.status_code == 409 and response.json()["code"] == "GROUP_SIZE_LIMIT_REACHED"
    as_user(client, world.admin)
    round_ = client.get(f"/api/rounds/{rid}").json()
    assert (round_["registered_six"], round_["registered_seven"], round_["registered"]) == (
        3,
        8,
        11,
    )
    admin_groups = client.get(f"/api/admin/rounds/{rid}/sextets").json()
    assert sum(len(g["members"]) for g in admin_groups) == 74
    monkeypatch.setattr(
        "app.services.allocation.database_now",
        lambda db: world.round.preferences_close_at + timedelta(seconds=1),
    )
    run = client.post(f"/api/admin/rounds/{rid}/allocate")
    assert run.status_code == 200, run.text
    allocations = client.get(f"/api/rounds/{rid}/results").json()["allocations"]
    assert len(allocations) == 11
    assert len({a["staff_id"] for a in allocations}) == 11
    assert all(a["status"] == "ALLOCATED" and a["partner_trio"] is None for a in allocations)
    with world.db() as db:
        assert verify(db, UUID(run.json()["id"])) == 11
    assert (
        client.post(f"/api/admin/rounds/{rid}/transition", json={"action": "publish"}).status_code
        == 200
    )
    as_user(client, world.users[0])
    assert len(client.get(f"/api/rounds/{rid}/results").json()["allocations"]) == 1
