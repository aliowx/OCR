from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ZoneBase(BaseModel):
    name: str | None = None
    tag: str | None = None
    parent_id: int | None = None
    floor_name: str | None = None
    floor_number: int | None = None
    capacity: int | None = None


class ZoneComplete(ZoneBase):
    empty: int | None = None
    full: int | None = None
    unknown: int | None = None
    pricings: list["ZonePrice"] = Field(default_factory=list)


class ZoneCreate(BaseModel):
    name: str
    tag: str | None = None
    floor_name: str | None = None
    floor_number: int | None = None
    capacity: int | None = None
    parent_id: int | None = None


class ZoneUpdate(ZoneBase):
    id: int


class ZoneInDBBase(ZoneComplete):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Zone(ZoneInDBBase):
    children: list[int] = []
    ancestors: list[int] = []


class ZoneInDB(ZoneInDBBase): ...


class ZonePriceBase(BaseModel):
    priority: int | None = None
    zone_id: int | None = None
    price_id: int | None = None


class ZonePriceCreate(ZonePriceBase):
    priority: int = Field(ge=1, le=100)
    zone_id: int
    price_id: int


class ZonePriceUpdate(ZonePriceBase): ...


class ZonePriceInDBBase(ZonePriceBase):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class ZonePrice(ZonePriceInDBBase): ...


class ZonePriceInDB(ZonePriceInDBBase): ...


class SetZonePriceInput(BaseModel):
    price_id: int
    priority: int = Field(ge=1, le=100)


class ZoneRule(ZoneBase):
    id: int | None = None


class ZonePramsFilters(BaseModel):
    input_name_zone: str | None = None
    input_name_floor: str | None = None
    input_number_floor: int | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
