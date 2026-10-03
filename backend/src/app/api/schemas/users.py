from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.api.schemas.common import Input, Name


class LoginInput(Input):
    login: Annotated[str, Field(min_length=2, max_length=254)]
    password: Annotated[
        str, StringConstraints(strip_whitespace=False, min_length=1, max_length=256)
    ]


class UserInput(Input):
    name: Name
    email: EmailStr
    is_captain: bool = False
    phone: Annotated[str, Field(max_length=32)] | None = None


class CaptainInput(Input):
    is_captain: bool


class CredentialDeliveryFailure(BaseModel):
    email: EmailStr
    code: str


class CredentialDispatchOut(BaseModel):
    dispatch_id: UUID
    eligible: int
    sent: int
    failed: list[CredentialDeliveryFailure]
    pending_remaining: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    login: str
    role: str
    is_captain: bool


class StudentAccessOut(BaseModel):
    login: str
    password: str


class AdminStudentOut(BaseModel):
    id: UUID
    name: str
    login: str
    email: str | None
    active: bool
    removed_at: datetime | None
    credentials_issued: bool
    is_captain: bool
    phone: str | None


class StudentSearchOut(BaseModel):
    id: UUID
    name: str
    login: str
    occupied: bool
