from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


# Shared properties
class RecordBase(BaseModel):
    plate: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    best_lpr_image_id: int | None = None
    best_plate_image_id: int | None = None
    price_model_id: int | None = None
    score: float | None = None
    parkinglot_id: int | None = None
    zone_id: int | None = None


# Properties to receive on item creation
class RecordCreate(RecordBase):
    plate: str
    start_time: datetime
    end_time: datetime
    price_model_id: int
    parkinglot_id: int
    zone_id: int


# Properties to receive on item update
class RecordUpdate(RecordBase):
    pass


# Properties shared by models stored in DB
class RecordInDBBase(RecordBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Record(RecordInDBBase):
    parkinglot_time: str | None = None
    parkinglot_price: float | None = None


# Properties properties stored in DB
class RecordInDB(RecordInDBBase):
    pass


class ParamsRecord(BaseModel):
    input_plate: str | None = None
    input_start_time_min: datetime | None = None
    input_start_time_max: datetime | None = None
    input_end_time_min: datetime | None = None
    input_end_time_max: datetime | None = None
    input_score: float | None = None
    skip: int | None = 0
    limit: int | None = 100
    asc: bool | None = False


class GetRecords(BaseModel):
    items: List[Record]
    all_items_count: int
