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
    img_entrance_id: int | None = None
    img_exit_id: int | None = None
    img_plate_entrance_id: int | None = None
    img_plate_exit_id: int | None = None
    score: float | None = None
    spot_id: int | None = None
    zone_id: int | None = None
    latest_status: StatusRecord | None = None
    camera_entrance_id: int | None = None
    camera_exit_id: int | None = None


# Properties to receive on item creation
class RecordCreate(RecordBase):
    plate: str
    start_time: datetime
    end_time: datetime
    zone_id: int
    latest_status: StatusRecord


# Properties to receive on item update
class RecordUpdate(RecordBase):
    latest_status: StatusRecord


# Properties shared by models stored in DB
class RecordInDBBase(RecordBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Record(RecordInDBBase):
    time_park: int | None = None
    zone_name: str | None = None
    camera_entrance: str | None = None
    camera_exit: str | None = None


# Properties properties stored in DB
class RecordInDB(RecordInDBBase):
    pass


class ParamsRecord(BaseModel):
    input_plate: str | None = None
    input_zone_id: int | None = None
    input_entrance_start_time: datetime | None = None
    input_entrance_end_time: datetime | None = None
    input_exit_start_time: datetime | None = None
    input_exit_end_time: datetime | None = None
    input_score: float | None = None
    input_camera_entrance_id: int | None = None
    input_camera_exit_id: int | None = None
    skip: int | None = 0
    limit: int | None = 100
    asc: bool | None = False


class GetRecords(BaseModel):
    items: List[Record]
    all_items_count: int


class JalaliDate(BaseModel):
    in_start_entrance_jalali_date: str | None = None
    in_end_entrance_jalali_date: str | None = None
    in_start_exit_jalali_date: str | None = None
    in_end_exit_jalali_date: str | None = None
