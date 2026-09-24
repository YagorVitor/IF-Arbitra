from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.common import Input


class SextetInput(Input):
    name: str = Field(min_length=2, max_length=80)
    # Index 0 = authenticated group leader; remaining members retain their chosen order.
    members: list[UUID] = Field(min_length=3, max_length=6)
    idempotency_key: UUID


class MemberOut(BaseModel):
    slot: int
    id: UUID
    name: str


class SextetOut(BaseModel):
    id: UUID
    name: str
    member_count: int
    round_id: UUID
    leader_id: UUID
    registration_completed_at: datetime
    priority_sequence: int
    members: list[MemberOut]
    preferences: list[UUID]
    preference_version: int
    preferences_submitted_at: datetime | None


class SextetSummaryOut(BaseModel):
    id: UUID
    name: str
    member_count: int
    registration_completed_at: datetime
    priority_sequence: int
