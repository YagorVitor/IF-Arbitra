from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditEventOut(BaseModel):
    id: int
    event_type: str
    occurred_at: datetime
    actor_name: str | None
    actor_user_id: UUID | None
    entity_type: str | None
    entity_id: str | None
    request_id: UUID
    payload: dict[str, Any]
    previous_state: dict[str, Any] | None
    resulting_state: dict[str, Any] | None


class AuditPageOut(BaseModel):
    next_cursor: int | None
    events: list[AuditEventOut]
