from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, FutureDatetime

from app.parking.schemas import ParkingZonePrice


class WeeklyDaysPriceModel(BaseModel):
    price_type: Literal["weekly"]

    saturday: int = 0
    sunday: int = 0
    monday: int = 0
    tuesday: int = 0
    wednesday: int = 0
    thursday: int = 0
    friday: int = 0


class ZonePriceModel(BaseModel):
    price_type: Literal["zone"]

    price: int = 0


class PriceBase(BaseModel):
    price_model: Union[WeeklyDaysPriceModel, ZonePriceModel] | None
    name: str | None = None
    name_fa: str | None = None
    entrance_fee: int | None = None
    hourly_fee: int | None = None
    daily_fee: int | None = None
    penalty_fee: int | None = None
    expiration_datetime: datetime | None = None
    parking_id: int | None = None


class PriceBaseComplete(PriceBase):
    pricings: list[ParkingZonePrice] = Field(default_factory=list)


class PriceCreate(PriceBase):
    price_model: Union[WeeklyDaysPriceModel, ZonePriceModel] = Field(
        ..., discriminator="price_type"
    )
    name: str
    name_fa: str
    entrance_fee: PositiveInt | None = None
    hourly_fee: PositiveInt | None = None
    daily_fee: PositiveInt | None = None
    penalty_fee: PositiveInt | None = None
    expiration_datetime: FutureDatetime | None = None
    zone_ids: list[int] = Field(default_factory=list)
    priority: int = Field(1, ge=1, le=100)


class PriceUpdate(PriceBase):
    entrance_fee: PositiveInt | None = None
    hourly_fee: PositiveInt | None = None
    daily_fee: PositiveInt | None = None
    penalty_fee: PositiveInt | None = None
    expiration_datetime: FutureDatetime | None = None
    zone_ids: list[int] = Field(default_factory=list)
    priority: int = Field(1, ge=1, le=100)


class PriceInDBBase(PriceBaseComplete):
    id: int
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Price(PriceInDBBase):
    pass


class CameraInDB(PriceInDBBase):
    pass


class GetPrice(BaseModel):
    items: list[Price]
    all_items_count: int
