from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Name = Annotated[str, Field(min_length=2, max_length=160)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ErrorOut(BaseModel):
    code: str
    message: str
    request_id: str
