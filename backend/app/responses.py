"""Public API shapes; secrets and ORM internals never enter these contracts."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class StaffOut(BaseModel):
    id: UUID
    name: str
    active: bool | None = None
    order: int | None = None


class StudentSearchOut(BaseModel):
    id: UUID
    name: str
    login: str
    occupied: bool


class RoundOut(BaseModel):
    id: UUID
    name: str
    status: str
    registration_opens_at: datetime
    registration_closes_at: datetime
    preferences_open_at: datetime
    preferences_close_at: datetime
    server_now: datetime
    registration_open: bool
    preferences_open: bool
    can_process: bool
    staff: list[StaffOut]
    registered: int
    with_preferences: int
    repechage: int
    capacity: int
    shortfall: int


class MemberOut(BaseModel):
    slot: int
    id: UUID
    name: str


class SextetOut(BaseModel):
    id: UUID
    name: str
    round_id: UUID
    leader_id: UUID
    registration_completed_at: datetime
    priority_sequence: int
    members: list[MemberOut]
    preferences: list[UUID]
    preference_version: int
    preferences_submitted_at: datetime | None


class PreferenceOut(BaseModel):
    version: int
    submitted_at: datetime


class SextetSummaryOut(BaseModel):
    id: UUID
    name: str
    registration_completed_at: datetime
    priority_sequence: int


class AllocationRunSummaryOut(BaseModel):
    id: UUID
    status: str
    input_fingerprint: str | None


class UnavailableStaffOut(BaseModel):
    staff_id: UUID
    sextet_id: UUID


class AllocationTraceOut(BaseModel):
    processing_order: int
    registration_completed_at: datetime
    priority_sequence: int
    ranking: list[UUID]
    fallback_order: list[UUID]
    unavailable: list[UnavailableStaffOut] | None = None
    chosen: UUID | None
    reason: str


class AllocationOut(BaseModel):
    id: UUID
    sextet_id: UUID
    sextet_name: str
    staff_name: str | None
    staff_id: UUID | None
    run_id: UUID
    status: str
    kind: str
    preference_position: int | None
    trace: AllocationTraceOut


class ResultsOut(BaseModel):
    published: bool
    allocations: list[AllocationOut]


class AllocationRunDetailOut(BaseModel):
    id: UUID
    status: str
    algorithm_version: str
    input_fingerprint: str | None
    snapshot: dict[str, Any]
    started_at: datetime
    finished_at: datetime | None


class AuditEventOut(BaseModel):
    id: int
    event_type: str
    occurred_at: datetime
    actor_name: str | None
    actor_user_id: UUID | None
    entity_id: str | None
    request_id: UUID
    payload: dict[str, Any]
    previous_state: dict[str, Any] | None
    resulting_state: dict[str, Any] | None


class AuditPageOut(BaseModel):
    next_cursor: int | None
    events: list[AuditEventOut]
