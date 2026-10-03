from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.common import Input


class ReservationInput(Input):
    staff_id: UUID | None
    reason: str = Field(min_length=10, max_length=1000, pattern=r"\S")


class ReservationOut(BaseModel):
    captain_id: UUID
    captain_name: str
    staff_id: UUID
    staff_name: str
    reason: str
    updated_at: datetime
    enabled: bool
