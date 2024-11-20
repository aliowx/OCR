from datetime import datetime, timezone
from typing import List, Optional
import pytz

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TypeEvent(str, Enum):
    sensor = "sensor"
    entranceDoor = "entranceDoor"
    exitDoor = "exitDoor"
    approaching_leaving_unknown = "ApproachingLeavingUnknown"  # approaching receding unknown vehicle for camera zoom in/out
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
    user_id: int | None = None
    invalid: bool | None = False

    additional_data: dict | None = None
    direction_info: dict | None = {}
    correct_ocr: str | None = None


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

    @field_validator("record_time", "created", mode="before")
    def convert_utc_to_iran_time(cls, value):

        if value:
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            # Define Iran Standard Time timezone
            iran_timezone = pytz.timezone("Asia/Tehran")

            # If value is naive (no timezone), localize it to UTC
            if value.tzinfo is None:
                # Localize the naive datetime to UTC
                utc_time = pytz.utc.localize(value)
            else:
                # If it's already timezone aware, convert to UTC
                utc_time = value.astimezone(pytz.utc)

            # Convert to Iran Standard Time
            return utc_time.astimezone(iran_timezone)
        return value

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Event(EventInDBBase):
    zone_name: str | None = None
    camera_name: str | None = None


# Properties properties stored in DB
class EventInDB(EventInDBBase):
    pass


class GetEvents(BaseModel):
    items: List[Event]
    all_items_count: int


class ParamsEvents(BaseModel):
    input_plate: str | None = None
    similar_plate: str | None = None
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
