from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum


class PlateStatus(str, Enum):
    valid = "valid"
    invalid = "invalid"


class PlateType(str, Enum):
    white = "white"
    black = "black"


class PlateBase(BaseModel):
    name: str | None = None
    plate: str | None = None
    expire_start: datetime | None = None
    expire_end: datetime | None = None
    type: PlateType | None = None
    status: PlateStatus | None = None


class PlateCreate(PlateBase): ...


class PlateUpdate(PlateBase): ...


class PlateInDBBase(PlateBase):
    id: int
    created: datetime | None = None
    modified: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PlateList(PlateInDBBase): ...


class ParamsPlate(BaseModel):
    input_name: str | None = None
    input_plate: str | None = None
    input_expire_start: datetime | None = None
    input_expire_end: datetime | None = None
    input_type: PlateType | None = None
    input_status: PlateStatus | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
