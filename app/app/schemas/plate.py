from datetime import datetime
from typing import List, Optional

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    full = "full"
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

    parkinglot_id: Optional[int] = None
    zone_id: Optional[int] = None

    price_model_id: Optional[int] = Field(None)

    type_status_parkinglot: Optional[Status] = Field(None)


class PlateCreate(PlateBase):
    plate: str
    record_time: datetime
    parkinglot_id: int
    zone_id: int
    camera_id: int
    lpr_image_id: int
    plate_image_id: int
    price_model_id: int
    type_status_parkinglot: Status


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
class Plate(PlateInDBBase):
    fancy: Optional[str]


# Properties properties stored in DB
class PlateInDB(PlateInDBBase):
    pass


class GetPlates(BaseModel):
    items: List[Plate]
    all_items_count: int
