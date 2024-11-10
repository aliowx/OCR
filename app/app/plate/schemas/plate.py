from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum


class PlateType(str, Enum):
    white = "white"
    black = "black"
    phone = "phone"


class PlateBase(BaseModel):
    name: str | None = None
    plate: str | None = None
    type: PlateType | None = None
    vehicle_model: str | None = None
    vehicle_color: str | None = None
    phone_number: str | None = None


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
    input_type: PlateType | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
