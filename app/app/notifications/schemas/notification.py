from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum
from app.plate.schemas import PlateList


class NotificationsBase(BaseModel):
    plate_list_id: int | None = None
    is_read: bool | None = False


class NotificationsCreate(NotificationsBase): ...


class NotificationsUpdate(NotificationsBase): ...


class NotificationsInDBBase(NotificationsBase):
    id: int
    created: datetime | None = None
    modified: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Notifications(NotificationsInDBBase):
    plate: PlateList | None = None


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
