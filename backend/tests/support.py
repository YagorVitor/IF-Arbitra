from datetime import timedelta
from uuid import uuid4


def as_user(client, user):
    client.cookies.set("if_arbitra_session", str(user.id))
    return client


def register(client, world, indices=range(6), key=None):
    students = [world.users[i] for i in indices]
    as_user(client, students[0])
    return client.post(
        f"/api/rounds/{world.round.id}/sextets",
        json={
            "name": "Sexteto teste",
            "members": [str(s.id) for s in students],
            "idempotency_key": str(key or uuid4()),
        },
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


def draft_payload(world):
    return {
        "name": "Rodada nova",
        "registration_opens_at": (world.now - timedelta(hours=1)).isoformat(),
        "registration_closes_at": (world.now + timedelta(hours=1)).isoformat(),
        "preferences_open_at": world.now.isoformat(),
        "preferences_close_at": (world.now + timedelta(hours=2)).isoformat(),
        "staff_ids": [str(s.id) for s in world.staff],
    }
