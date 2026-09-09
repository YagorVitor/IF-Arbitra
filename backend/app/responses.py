"""Public API shapes; secrets and ORM internals never enter these contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StaffOut(BaseModel):
    id: UUID
    name: str
    active: bool | None = None
    order: int | None = None


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
