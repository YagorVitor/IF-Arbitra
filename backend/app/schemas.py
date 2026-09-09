from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, Field(min_length=2, max_length=160)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginInput(Input):
    login: Name
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=1, max_length=256)
    ]


class UserInput(Input):
    name: Name
    login: Name
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=12, max_length=256)
    ]


class StaffInput(Input):
    name: Name
    active: bool = True


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


class SextetInput(Input):
    name: str = Field(min_length=2, max_length=80)
    # Index 0 = Trio A leader and administrator; index 3 = Trio B leader.
    members: list[UUID] = Field(min_length=6, max_length=6)
    idempotency_key: UUID


class PreferencesInput(Input):
    staff_ids: list[UUID] = Field(min_length=1, max_length=500)
    expected_version: int = Field(ge=0)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    login: str
    role: str


class ErrorOut(BaseModel):
    code: str
    message: str
    request_id: str
