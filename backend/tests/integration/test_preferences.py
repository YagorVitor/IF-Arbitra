from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    AuditEvent,
    PreferenceSubmission,
)
from tests.support import register

pytestmark = pytest.mark.integration


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
    monkeypatch.setattr(
        "app.services.rounds.database_now", lambda db: world.round.preferences_close_at
    )
    assert client.put(path, json={"staff_ids": ids, "expected_version": 2}).status_code == 409
    with world.db() as db:
        preference_events = list(
            db.scalars(
                select(AuditEvent.event_type)
                .where(
                    AuditEvent.entity_type == "SEXTET",
                    AuditEvent.entity_id == first["id"],
                    AuditEvent.event_type.in_(["PREFERENCE_SUBMITTED", "PREFERENCE_UPDATED"]),
                )
                .order_by(AuditEvent.id)
            )
        )
        assert preference_events == ["PREFERENCE_SUBMITTED", "PREFERENCE_UPDATED"]
        assert db.scalar(
            select(AuditEvent).where(
                AuditEvent.event_type == "OPERATION_REJECTED",
                AuditEvent.payload["code"].astext == "PREFERENCE_WINDOW_CLOSED",
            )
        )


def test_ranking_db_constraint_rejects_partial_submission(world, client):
    sextet = register(client, world).json()
    with pytest.raises(IntegrityError), world.db.begin() as db:
        db.add(
            PreferenceSubmission(
                sextet_id=UUID(sextet["id"]),
                round_id=world.round.id,
                version=1,
                submitted_at=world.now,
            )
        )
