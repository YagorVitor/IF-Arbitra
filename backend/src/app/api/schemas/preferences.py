from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.common import Input


class PreferencesInput(Input):
    staff_ids: list[UUID] = Field(min_length=1, max_length=500)
    expected_version: int = Field(ge=0)


class PreferenceOut(BaseModel):
    version: int
    submitted_at: datetime
