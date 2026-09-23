from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


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
