from datetime import datetime
from typing import List, Optional

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class TypeCamera(str, Enum):
    sensor = "sensor"
    entranceDoor = "entranceDoor"
    exitDoor = "exitDoor"


# Shared properties
class PlateBase(BaseModel):
    plate: Optional[str] = None

    record_time: Optional[datetime] = None

    plate_image_id: Optional[int] = None
    lpr_image_id: Optional[int] = None
    record_id: Optional[int] = None

    camera_id: Optional[int] = Field(None, ge=1)

    spot_id: Optional[int] = None
    zone_id: Optional[int] = None

    price_model_id: Optional[int] = Field(None)
    type_camera: TypeCamera | None = None


class PlateCreate(PlateBase):
    plate: str
    record_time: datetime
    spot_id: int | None = None
    zone_id: int
    camera_id: int
    lpr_image_id: int
    plate_image_id: int
    price_model_id: int | None = None
    type_camera: TypeCamera


# Properties to receive on item update
class PlateUpdate(PlateBase):
    pass


# Properties shared by models stored in DB
class PlateInDBBase(PlateBase):
    id: int
    created: Optional[datetime]
    modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Plate(PlateInDBBase): ...


# Properties properties stored in DB
class PlateInDB(PlateInDBBase):
    pass


class GetPlates(BaseModel):
    items: List[Plate]
    all_items_count: int


class ParamsPlates(BaseModel):
    input_plate: str | None = None
    input_camera_serial: str | None = None
    input_time_min: datetime | None = None
    input_time_max: datetime | None = None
    input_camera_id: int | None = None
    input_record_id: int | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip


class ReportDoor(BaseModel):
    count: int | None = None
    type_camera: TypeCamera | None = None
    camera_name: str | None = None
