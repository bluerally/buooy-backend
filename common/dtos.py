from pydantic import BaseModel, Field
from typing import TypeVar, Optional

T = TypeVar("T")


class BaseResponse[T](BaseModel):
    status_code: int = None
    message: str = ""
    data: Optional[T] = Field(default=None)
