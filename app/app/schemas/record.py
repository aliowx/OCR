from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator, Field
import pytz


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
    zone_id: int
    latest_status: StatusRecord


# Properties to receive on item update
class RecordUpdate(RecordBase):
    latest_status: StatusRecord


class RecordUpdatePlate(BaseModel):
    plate: str
    latest_status: StatusRecord | None = None
    end_time: datetime | None = None


# Properties shared by models stored in DB
class RecordInDBBase(RecordBase):
    id: int
    created: datetime | None
    modified: datetime | None

    @field_validator("start_time", "end_time", "created", mode="before")
    def convert_utc_to_iran_time(cls, value):

        if value:
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            # Define Iran Standard Time timezone
            iran_timezone = pytz.timezone("Asia/Tehran")

            # If value is naive (no timezone), localize it to UTC
            if value.tzinfo is None:
                # Localize the naive datetime to UTC
                utc_time = pytz.utc.localize(value)
            else:
                # If it's already timezone aware, convert to UTC
                utc_time = value.astimezone(pytz.utc)

            # Convert to Iran Standard Time
            return utc_time.astimezone(iran_timezone)
        return value

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Record(RecordInDBBase):
    time_park: int | None = None
    zone_name: str | None = None
    camera_entrance: str | None = None
    camera_exit: str | None = None


class RecordForWS(RecordBase):
    time_park: int | None = None
    zone_name: str | None = None
    camera_entrance: str | None = None
    camera_exit: str | None = None

    @field_validator("start_time", "end_time", mode="before")
    def convert_utc_to_iran_time(cls, value):

        if value:
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            # Define Iran Standard Time timezone
            iran_timezone = pytz.timezone("Asia/Tehran")

            # If value is naive (no timezone), localize it to UTC
            if value.tzinfo is None:
                # Localize the naive datetime to UTC
                utc_time = pytz.utc.localize(value)
            else:
                # If it's already timezone aware, convert to UTC
                utc_time = value.astimezone(pytz.utc)

            # Convert to Iran Standard Time
            return utc_time.astimezone(iran_timezone)
        return value


# Properties properties stored in DB
class RecordInDB(RecordInDBBase):
    pass


class SortBy(str, Enum):
    entrance_time = "entrance_time"
    exit_time = "exit_time"


class ParamsRecord(BaseModel):
    input_plate: str | None = None
    similar_plate: str | None = None
    input_zone_id: int | None = None
    input_entrance_start_time: datetime | None = None
    input_entrance_end_time: datetime | None = None
    input_exit_start_time: datetime | None = None
    input_exit_end_time: datetime | None = None
    input_score: float | None = None
    sort_by: SortBy | None = SortBy.exit_time
    input_entrance_persent_time: datetime | None = None
    input_exit_persent_time: datetime | None = None
    skip: int | None = 0
    limit: int | None = None
    asc: bool | None = True


class GetRecords(BaseModel):
    items: List[Record]
    all_items_count: int


class JalaliDate(BaseModel):
    in_start_entrance_jalali_date: str | None = None
    in_end_entrance_jalali_date: str | None = None
    in_start_exit_jalali_date: str | None = None
    in_end_exit_jalali_date: str | None = None


class RecordExcelItem(BaseModel):
    plate: str | None = Field(None, serialization_alias="شماره پلاک")
    start_date: str | None = Field(None, serialization_alias="تاریخ ورود")
    start_time: str | None = Field(None, serialization_alias="زمان ورود")
    end_date: str | None = Field(None, serialization_alias="تاریخ خروج")
    end_time: str | None = Field(None, serialization_alias="زمان خروج")
    time_park: float | None = Field(
        None, serialization_alias="مدت زمان توقف (دقیقه)"
    )
    zone_name: str | None = Field(None, serialization_alias="محل پارک")
    camera_entrance: str | None = Field(
        None, serialization_alias="دوربین ورودی"
    )
    camera_exit: str | None = Field(None, serialization_alias="دوربین خروجی")
    latest_status: str | None = Field(None, serialization_alias="وضعیت")

class RecordExcelItemForPolice(BaseModel):
    seri: str | None = Field(None, serialization_alias="SERI")
    hrf: str | None = Field(None, serialization_alias="HRF")
    serial: str | None = Field(None, serialization_alias="SERIAL")
    iran: str | None = Field(None, serialization_alias="IRAN")
