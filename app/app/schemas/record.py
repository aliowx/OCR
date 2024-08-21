from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel, ConfigDict


class StatusRecord(str, Enum):
    finished = "finished"
    unfinished = "unfinished"
    unknown = "unknown"


# Shared properties
class RecordBase(BaseModel):
    plate: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    best_lpr_image_id: int | None = None
    best_plate_image_id: int | None = None
    price_model_id: int | None = None
    score: float | None = None
    spot_id: int | None = None
    zone_id: int | None = None
    latest_status: StatusRecord | None = None


# Properties to receive on item creation
class RecordCreate(RecordBase):
    plate: str
    start_time: datetime
    end_time: datetime
    price_model_id: int | None = None
    spot_id: int | None = None
    zone_id: int
    latest_status: StatusRecord


# Properties to receive on item update
class RecordUpdate(BaseModel):
    latest_status: StatusRecord


# Properties shared by models stored in DB
class RecordInDBBase(RecordBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Record(RecordInDBBase):
    total_time: str | None = None
    # total_price: float | None = None


# Properties properties stored in DB
class RecordInDB(RecordInDBBase):
    pass


class ParamsRecord(BaseModel):
    input_plate: str | None = None
    input_start_time: datetime | None = None
    input_end_time: datetime | None = None
    input_score: float | None = None
    input_status_record: StatusRecord | None = None
    skip: int | None = 0
    limit: int | None = 100
    asc: bool | None = False


class GetRecords(BaseModel):
    items: List[Record]
    all_items_count: int
