from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParkingZoneBase(BaseModel):
    name: str | None = None
    tag: str | None = None
    parking_id: int | None = None
    parent_id: int | None = None


class ParkingZoneComplete(ParkingZoneBase):
    parent: ParkingZoneBase | None = None
    children: list["ParkingZone"] = Field(default_factory=list)


class ParkingZoneCreate(ParkingZoneBase):
    name: str


class ParkingZoneUpdate(ParkingZoneBase): ...


class ParkingZoneInDBBase(ParkingZoneComplete):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class ParkingZone(ParkingZoneInDBBase): ...


class ParkingZoneInDB(ParkingZoneInDBBase): ...
