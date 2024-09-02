from datetime import datetime
from app.parking.schemas import Zone
from pydantic import BaseModel, ConfigDict


class Capacity(BaseModel):
    total: int | None = None
    empty: int | None = None
    full: int | None = None
    total_today_park: int | None = None


class AverageTimeDetail(BaseModel):
    time: int | None = None
    compare: int | None = None


class AverageTime(BaseModel):
    avrage_all_time: str | None = None
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
    count_entrance_exit_door: list | None = []


class ZoneReport(Zone):
    todat_referred: int | None = 0
    avrage_stop_time_today: int | None = 0
    avrage_amount_bill_today: float | None = 0
    income_today_parking: float | None = 0
