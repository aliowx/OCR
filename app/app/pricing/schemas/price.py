from datetime import datetime, time as TIME

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PositiveInt
from enum import Enum, IntEnum
from app.parking.schemas import ZonePrice


class PriceBase(BaseModel):
    name: str | None = None
    name_fa: str | None = None
    entrance_fee: float | None = None
    hourly_fee: float | None = None




class PriceCreate(PriceBase):
    name: str
    name_fa: str

    zone_ids: list[int] = Field(default_factory=list)
    priority: int = Field(1, ge=1, le=100)


class PriceUpdate(PriceBase):
    zone_ids: list[int] = Field(default_factory=list)
    priority: int = Field(1, ge=1, le=100)


class PriceInDBBase(PriceBase):
    id: int
    created: datetime | None = None
    modified: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Price(PriceInDBBase):
    zone_name : str | None = None


class CameraInDB(PriceInDBBase):
    pass


class ReadPricesParams(BaseModel):
    name: str | None = None
    name_fa: str | None = None
    zone_id: int | None = None

    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
