from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from enum import Enum
from app.plate.schemas import PlateList
from app.schemas.event import Event
import pytz

class TypeNotice(str, Enum):
    black_list = "black_list"
    equipment = "equipment"


class NotificationsBase(BaseModel):
    plate_list_id: int | None = None
    is_read: bool | None = False
    event_id: int | None = None
    text: str | None = None
    type_notice: TypeNotice | None = None


class NotificationsCreate(NotificationsBase): ...


class NotificationsUpdate(BaseModel):
    is_read: bool | None = False


class NotificationsInDBBase(NotificationsBase):
    id: int
    created: datetime | None = None
    modified: datetime | None = None

    @field_validator("created", mode="before")
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


class Notifications(NotificationsInDBBase):
    plate: PlateList | None = None
    event: Event | None = None
    zone_name: str | None = None
    camera_tag: str | None = None
    status: str | None = None


class ParamsNotifications(BaseModel):
    input_read: bool | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
