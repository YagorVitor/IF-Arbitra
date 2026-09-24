from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.api.schemas.common import Input, Name


class StaffCreateInput(Input):
    name: Name
    email: EmailStr


class StaffUpdateInput(Input):
    name: Name
    active: bool = True
    email: EmailStr | None = None


class StaffOut(BaseModel):
    id: UUID
    name: str
    email: str | None = None
    active: bool | None = None
    order: int | None = None
