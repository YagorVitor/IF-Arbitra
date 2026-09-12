from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.api.schemas.common import Input, Name


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


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    login: str
    role: str


class StudentSearchOut(BaseModel):
    id: UUID
    name: str
    login: str
    occupied: bool
