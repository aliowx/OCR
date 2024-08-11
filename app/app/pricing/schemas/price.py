from datetime import datetime

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PositiveInt
from enum import Enum, IntEnum
from app.parking.schemas import ZonePrice


class FreeFeeTiming(IntEnum):
    fifteen = 15
    thirty_minutes = 30
    one_hour = 60
    one_hour_thirty_minutes = 90


class WeeklyDays(BaseModel):
    saturday: int | None = None
    sunday: int | None = None
    monday: int | None = None
    tuesday: int | None = None
    wednesday: int | None = None
    thursday: int | None = None
    friday: int | None = None


class Weekly(BaseModel):
    week_fixed: WeeklyDays | None = None
    week_days: WeeklyDays | None = None


class DurtionTime(BaseModel):
    start_time: int | None = None
    end_time: int | None = None
    price: int | None = None


class Staircase(BaseModel):
    hour_durtion: list[DurtionTime] | None = None
    minutes_durtion: list[DurtionTime] | None = None
    one_day_price: int | None = None


class Proven(BaseModel):
    weekly: Weekly
    free_fee_timing: FreeFeeTiming = FreeFeeTiming.thirty_minutes
    free_fee_first_park: bool | None = None
    one_day_price: int | None = None


class Entrance(Weekly):
    free_fee_timing: FreeFeeTiming = FreeFeeTiming.fifteen


class Hourly(BaseModel):
    staircase: Staircase | None = None
    proven: Proven | None = None


class ModelPrice(BaseModel):
    entrance: Entrance | None = None
    hourly: Hourly | None = None


class PriceBase(BaseModel):
    name: str | None = None
    name_fa: str | None = None
    price_model: ModelPrice | None = None


class PriceBaseComplete(PriceBase):
    pricings: list[ZonePrice] = Field(default_factory=list)


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
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Price(PriceInDBBase):
    pass


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
