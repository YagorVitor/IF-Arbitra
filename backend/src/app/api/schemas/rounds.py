from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from app.api.schemas.common import Input, Name
from app.api.schemas.staff import StaffOut


class RoundInput(Input):
    name: Name
    registration_opens_at: AwareDatetime
    registration_closes_at: AwareDatetime
    preferences_open_at: AwareDatetime
    preferences_close_at: AwareDatetime
    staff_ids: list[UUID] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid(self):
        if not (
            self.registration_opens_at < self.registration_closes_at <= self.preferences_close_at
            and self.preferences_open_at < self.preferences_close_at
        ):
            raise ValueError("Os prazos da rodada são inconsistentes.")
        if len(self.staff_ids) != len(set(self.staff_ids)):
            raise ValueError("Há servidores repetidos.")
        return self


class TransitionInput(Input):
    action: Literal["open", "publish", "archive"]


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
