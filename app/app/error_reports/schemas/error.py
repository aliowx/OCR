from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ErrorBase(BaseModel):
    record_id: int | None = None
    bill_id: int | None = None
    correct_plate: str | None = None


class ErrorCreate(ErrorBase): ...


class ErrorUpdate(ErrorBase):
    correct_plate: str


class ErrorInDBBase(ErrorBase):
    id: Optional[int] = None
    created: datetime | None = None
    modified: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class Error(ErrorInDBBase): ...


class ParamsError(BaseModel):
    input_plate: str | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
