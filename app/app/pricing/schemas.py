from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, FutureDatetime, PositiveInt

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


class ReadPricesFilter(BaseModel):
    name__contains: str | None = None
    name_fa__contains: str | None = None
    parking_id__eq: int | None = None
    zone_id__eq: int | None = None
    expiration_datetime__gte: str | None = None
    expiration_datetime__lte: str | None = None
    created__gte: str | None = None
    created__lte: str | None = None
    limit: int | None = 100
    skip: int = 0

    @property
    def join_pricezone(self) -> bool:
        return self.zone_id__eq is not None


class ReadPricesParams(BaseModel):
    name: str | None = None
    name_fa: str | None = None
    parking_id: int | None = None
    zone_id: int | None = None
    expiration_datetime_start: datetime | None = None
    expiration_datetime_end: datetime | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip

    @property
    def db_filters(self) -> ReadPricesFilter:
        filters = ReadPricesFilter(limit=self.size, skip=self.skip)
        if self.name:
            filters.name__contains = self.name
        if self.name_fa:
            filters.name_fa__contains = self.name_fa
        if self.parking_id:
            filters.parking_id__eq = self.parking_id
        if self.zone_id:
            filters.zone_id__eq = self.zone_id
        if self.expiration_datetime_start:
            filters.expiration_datetime__gte = self.expiration_datetime_start
        if self.expiration_datetime_end:
            filters.expiration_datetime__lte = self.expiration_datetime_end
        if self.start_date:
            filters.created__gte = self.start_date
        if self.end_date:
            filters.created__lte = self.end_date
        return filters
