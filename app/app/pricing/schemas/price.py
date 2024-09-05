from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PriceBase(BaseModel):
    name: str | None = None
    entrance_fee: float | None = None
    hourly_fee: float | None = None


class PriceCreate(PriceBase):
    name: str
    zone_ids: list[int] = None


class PriceUpdate(PriceBase): ...


class PriceInDBBase(PriceBase):
    id: int
    created: datetime | None = None
    modified: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Price(PriceInDBBase): ...


class CameraInDB(PriceInDBBase):
    pass


class ReadPricesParams(BaseModel):
    name: str | None = None

    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
