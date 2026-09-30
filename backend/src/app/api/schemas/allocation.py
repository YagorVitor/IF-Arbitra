from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.common import Input
from app.api.schemas.sextets import MemberOut


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
    preference_pass: int | None = None
    paired_with: UUID | None = None


class PairedTrioOut(BaseModel):
    id: UUID
    name: str
    members: list[MemberOut]


class AllocationOut(BaseModel):
    id: UUID
    sextet_id: UUID
    sextet_name: str
    staff_name: str | None
    staff_id: UUID | None
    staff_slot: int
    partner_trio: PairedTrioOut | None = None
    run_id: UUID
    status: str
    kind: str
    preference_position: int | None
    trace: AllocationTraceOut
    manually_adjusted: bool = False


class ResultsOut(BaseModel):
    published: bool
    allocations: list[AllocationOut]
    revision: int = 0
    adjustment_reason: str | None = None


class AssignmentInput(Input):
    allocation_id: UUID
    staff_id: UUID | None


class AdjustmentInput(Input):
    expected_revision: int = Field(ge=0)
    reason: str = Field(min_length=10, max_length=1000)
    assignments: list[AssignmentInput] = Field(min_length=1, max_length=1000)


class AdjustmentOut(BaseModel):
    revision: int


class AllocationRunDetailOut(BaseModel):
    id: UUID
    status: str
    algorithm_version: str
    input_fingerprint: str | None
    snapshot: dict[str, Any]
    started_at: datetime
    finished_at: datetime | None
