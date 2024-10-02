from datetime import datetime, timezone
from typing import List, Optional

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class TypeEvent(str, Enum):
    sensor = "sensor"
    entranceDoor = "entranceDoor"
    exitDoor = "exitDoor"
    admin_exitRegistration_and_billIssuance = "exitReg_billIssue"
    admin_exitRegistration = "exitReg"


# Shared properties
class EventBase(BaseModel):
    plate: Optional[str] = None

    record_time: Optional[datetime] = None

    plate_image_id: Optional[int] = None
    lpr_image_id: Optional[int] = None
    record_id: Optional[int] = None

    camera_id: Optional[int] = None

    spot_id: Optional[int] = None
    zone_id: Optional[int] = None

    type_event: TypeEvent | None = None


class EventCreate(EventBase):
    plate: str
    record_time: datetime = datetime.now(timezone.utc).replace(tzinfo=None)
    zone_id: int
    type_event: TypeEvent


# Properties to receive on item update
class EventUpdate(EventBase):
    pass


# Properties shared by models stored in DB
class EventInDBBase(EventBase):
    id: int
    created: Optional[datetime]
    modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Event(EventInDBBase): ...


# Properties properties stored in DB
class EventInDB(EventInDBBase):
    pass


class GetEvents(BaseModel):
    items: List[Event]
    all_items_count: int


class ParamsEvents(BaseModel):
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
    type_event: TypeEvent | None = None
    camera_name: str | None = None
