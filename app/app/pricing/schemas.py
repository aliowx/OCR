from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field


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
    name: str | None
    name_fa: str | None
    parking_id: int | None = None


class PriceCreate(PriceBase):
    price_model: Union[WeeklyDaysPriceModel, ZonePriceModel] = Field(
        ..., discriminator="price_type"
    )
    name: str
    name_fa: str


class PriceUpdate(PriceBase):
    pass


class PriceInDBBase(PriceBase):
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
