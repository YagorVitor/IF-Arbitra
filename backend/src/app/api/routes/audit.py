from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.dependencies import admin
from app.api.schemas.audit import AuditPageOut
from app.core.errors import DomainError
from app.db.models import (
    AuditEvent,
    User,
)
from app.db.session import SessionFactory

router = APIRouter()


@router.get("/admin/audit", response_model=AuditPageOut, tags=["Auditoria"])
def audit_events(
    event: str | None = Query(None, max_length=80),
    entity_type: str | None = Query(None, max_length=40),
    entity: str | None = Query(None, max_length=80),
    actor: UUID | None = None,
    request_id: UUID | None = None,
    before_id: int | None = Query(None, gt=0),
    since: str | None = Query(None, max_length=40),
    until: str | None = Query(None, max_length=40),
    user=Depends(admin),
):
    from datetime import datetime

    stmt = select(AuditEvent, User.name).outerjoin(User, AuditEvent.actor_user_id == User.id)
    for column, value in [
        (AuditEvent.event_type, event),
        (AuditEvent.entity_type, entity_type),
        (AuditEvent.entity_id, entity),
        (AuditEvent.actor_user_id, actor),
        (AuditEvent.request_id, str(request_id) if request_id else None),
    ]:
        if value:
            stmt = stmt.where(column == value)
    try:
        start = datetime.fromisoformat(since) if since else None
        end = datetime.fromisoformat(until) if until else None
        if any(d is not None and d.utcoffset() is None for d in (start, end)):
            raise ValueError("Timezone required")
        if start and end and start > end:
            raise ValueError("Inverted interval")
        if since:
            stmt = stmt.where(AuditEvent.occurred_at >= start)
        if until:
            stmt = stmt.where(AuditEvent.occurred_at <= end)
    except ValueError:
        raise DomainError(
            "INVALID_DATE", "Informe datas com fuso e início anterior ou igual ao fim.", 422
        ) from None
    if before_id:
        stmt = stmt.where(AuditEvent.id < before_id)
    with SessionFactory() as db:
        rows = db.execute(stmt.order_by(AuditEvent.id.desc()).limit(51)).all()
        return {
            "next_cursor": rows[49][0].id if len(rows) > 50 else None,
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "occurred_at": e.occurred_at,
                    "actor_name": name,
                    "actor_user_id": e.actor_user_id,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "request_id": e.request_id,
                    "payload": e.payload,
                    "previous_state": e.previous_state,
                    "resulting_state": e.resulting_state,
                }
                for e, name in rows[:50]
            ],
        }
