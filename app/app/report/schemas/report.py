from datetime import datetime
from app.parking.schemas import Zone
from pydantic import BaseModel
from enum import Enum


class Timing(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class DoorType(str, Enum):
    entry = "entry"
    exit = "exit"


class Capacity(BaseModel):
    total: int | None = None
    empty: int | None = None
    full: int | None = None
    unknown: int | None = None
    count_referred: int | None = None
    total_amount_bill: float | None = None
    time_minute_park: int | None = None
    len_zone: int | None = None
    effective_utilization_rate: float | None = None


class AverageTimeDetail(BaseModel):
    time: int | None = None
    compare: int | None = None


class AverageTime(BaseModel):
    avrage_all_time: int | None = None
    avrage_today: AverageTimeDetail | None = None
    avrage_one_week_ago: AverageTimeDetail | None = None
    avrage_one_month_ago: AverageTimeDetail | None = None
    avrage_six_month_ago: AverageTimeDetail | None = None
    avrage_one_year_ago: AverageTimeDetail | None = None


class referred_timing(BaseModel):
    week: list | None = []
    month: list | None = []
    six_month: list | None = []
    year: list | None = []


class Referred(BaseModel):
    list_referred: dict | None = None


class MaxTimePark(BaseModel):
    plate: str | None = None
    created: datetime | None = None
    time_as_minute: float | None = None


class ListMaxTimePark(BaseModel):
    total_max_time_park: list[MaxTimePark] = [MaxTimePark]


class CountEntranceExitDoor(BaseModel):
    count_entrance: dict | None = {}
    count_exit: dict | None = {}
    total_entrance: int | None = None
    total_exit: int | None = None


class JalaliDate(BaseModel):
    in_start_jalali_date: str | None = None
    in_end_jalali_date: str | None = None


class ZoneReport(Zone):
    total_referred: int | None = 0
    time_park_minute_today: int | None = 0
    avrage_amount_bill_today: float | None = 0
    income_today_parking: float | None = 0
    effective_utilization_rate: float | None = 0
