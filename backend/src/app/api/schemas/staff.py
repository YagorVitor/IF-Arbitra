from uuid import UUID

from pydantic import BaseModel

from app.api.schemas.common import Input, Name


class StaffInput(Input):
    name: Name
    active: bool = True


class StaffOut(BaseModel):
    id: UUID
    name: str
    active: bool | None = None
    order: int | None = None
