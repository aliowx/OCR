from datetime import datetime

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from app.parking.schemas import ParkingZonePrice


class WeeklyDays(BaseModel):
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None


class PriceBase(BaseModel):
    weekly_days: WeeklyDays | None = None
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
    weekly_days: WeeklyDays | None = None
    name: str
    name_fa: str
    entrance_fee: PositiveInt | None = None
    hourly_fee: PositiveInt | None = None
    daily_fee: PositiveInt | None = None
    penalty_fee: PositiveInt | None = None
    expiration_datetime: datetime | None = None
    zone_ids: list[int] = Field(default_factory=list)
    priority: int = Field(1, ge=1, le=100)


class PriceUpdate(PriceBase):
    entrance_fee: PositiveInt | None = None
    hourly_fee: PositiveInt | None = None
    daily_fee: PositiveInt | None = None
    penalty_fee: PositiveInt | None = None
    expiration_datetime: datetime | None = None
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


# class ReadPricesFilter(BaseModel):
#     name__contains: str | None = None
#     name_fa__contains: str | None = None
#     parking_id__eq: int | None = None
#     zone_id__eq: int | None = None
#     expiration_datetime__gte: str | None = None
#     expiration_datetime__lte: str | None = None
#     created__gte: str | None = None
#     created__lte: str | None = None
#     limit: int | None = 100
#     skip: int = 0

    


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


    # @property
    # def db_filters(self) -> ReadPricesFilter:
    #     filters = ReadPricesFilter(limit=self.size, skip=self.skip)
    #     if self.name:
    #         filters.name__contains = self.name
    #     if self.name_fa:
    #         filters.name_fa__contains = self.name_fa
    #     if self.parking_id:
    #         filters.parking_id__eq = self.parking_id
    #     if self.zone_id:
    #         filters.zone_id__eq = self.zone_id
    #     if self.expiration_datetime_start:
    #         filters.expiration_datetime__gte = self.expiration_datetime_start
    #     if self.expiration_datetime_end:
    #         filters.expiration_datetime__lte = self.expiration_datetime_end
    #     if self.start_date:
    #         filters.created__gte = self.start_date
    #     if self.end_date:
    #         filters.created__lte = self.end_date
    #     return filters
