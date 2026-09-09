from enum import StrEnum

from app.db import SessionFactory
from app.models import AuditEvent


class Event(StrEnum):
    LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    LOGOUT = "AUTH_LOGOUT"
    SEXTET_ATTEMPT = "SEXTET_CREATION_ATTEMPT"
    SEXTET_CREATED = "SEXTET_CREATED"
    PREFERENCE_ATTEMPT = "PREFERENCE_SUBMISSION_ATTEMPT"
    PREFERENCE_SUBMITTED = "PREFERENCE_SUBMITTED"
    PREFERENCE_UPDATED = "PREFERENCE_UPDATED"
    REJECTED = "OPERATION_REJECTED"
    ALLOCATION_STARTED = "ALLOCATION_STARTED"
    GROUP_PROCESSED = "ALLOCATION_GROUP_PROCESSED"
    ALLOCATION_FINISHED = "ALLOCATION_FINISHED"
    ALLOCATION_FAILED = "ALLOCATION_FAILED"
    ADMIN = "ADMIN_ACTION"


def record(
    db, request, event, entity=None, payload=None, before=None, after=None, *, entity_type=None
):
    db.add(
        AuditEvent(
            event_type=str(event),
            actor_user_id=getattr(request.state, "actor_id", None),
            entity_type=entity_type,
            entity_id=str(entity) if entity else None,
            request_id=request.state.request_id,
            payload=payload or {},
            previous_state=before,
            resulting_state=after,
        )
    )


def independent(request, event, entity=None, payload=None, *, entity_type=None):
    # Attempts survive business rollback. No request bodies, cookies, IPs or credentials are stored.
    with SessionFactory.begin() as db:
        record(db, request, event, entity, payload, entity_type=entity_type)
