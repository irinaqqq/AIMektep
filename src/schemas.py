from pydantic import BaseModel
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

class ListResponse(BaseModel, Generic[T]):
    data: list[T]
    total: Optional[int] = None

class StatusResponse(BaseModel):
    status: bool = True
    message: Optional[str] = None