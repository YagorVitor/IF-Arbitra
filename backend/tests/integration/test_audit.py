from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    AuditEvent,
)
from tests.support import as_user, register

pytestmark = pytest.mark.integration


def test_audit_append_only_and_ready(world, client):
    sextet = register(client, world).json()
    assert client.get("/ready").status_code == 200
    as_user(client, world.admin)
    events = client.get("/api/admin/audit", params={"entity_type": "SEXTET"}).json()["events"]
    assert any(e["entity_id"] == sextet["id"] for e in events)
    assert {e["entity_type"] for e in events} == {"SEXTET"}
    for sql in [
        "DELETE FROM audit_events",
        "UPDATE audit_events SET payload='{}'::jsonb",
        "TRUNCATE audit_events",
    ]:
        with pytest.raises(IntegrityError), world.db.begin() as db:
            db.execute(text(sql))


@pytest.mark.parametrize(
    "params",
    [
        {"since": "2026-09-10"},
        {"since": "2026-09-10T10:00:00"},
        {"since": "invalid"},
        {"since": "2026-09-11T00:00:00Z", "until": "2026-09-10T00:00:00Z"},
    ],
)
def test_audit_rejects_ambiguous_dates(world, client, params):
    as_user(client, world.admin)
    response = client.get("/api/admin/audit", params=params)
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_DATE"


def test_audit_filters_and_cursor_do_not_skip_events(world, client):
    with world.db.begin() as db:
        db.add_all(
            AuditEvent(
                event_type="CURSOR_TEST",
                entity_type="USER",
                entity_id=str(world.users[0].id),
                actor_user_id=world.admin.id,
                request_id=str(uuid4()),
                payload={"i": i},
            )
            for i in range(55)
        )
    as_user(client, world.admin)
    params = {
        "event": "CURSOR_TEST",
        "actor": str(world.admin.id),
        "since": (world.now - timedelta(minutes=1)).isoformat(),
    }
    first = client.get("/api/admin/audit", params=params).json()
    second = client.get(
        "/api/admin/audit", params={**params, "before_id": first["next_cursor"]}
    ).json()
    assert len(first["events"]) == 50 and len(second["events"]) == 5
    assert len({e["id"] for e in first["events"] + second["events"]}) == 55
    assert second["next_cursor"] is None
