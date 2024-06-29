from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportBase(BaseModel): ...


class ZoneLots(BaseModel):
    zone_name: str = None
    list_lots: list = None
    capacity: int = None
    capacity_empty: int = None
    record: list = None


class ReadZoneLotsParams(BaseModel):
    input_floor_number: int | None = None
    input_name_zone: str | None = None
    input_name_sub_zone: str | None = None
    input_start_time: datetime | None = None
    input_end_time: datetime | None = None
    input_zone_id: int | None = None
    size: int | None = 100
    page: int | None = 1
    asc: bool | None = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip


class ParamsRecordMoment(BaseModel):
    input_camera_code: str | None = None
    input_plate: str | None = None
    input_name_zone: str | None = None
    input_name_sub_zone: str | None = None
    input_floor_number: int | None = None


class ParamsRecordMomentFilters(BaseModel):
    input_camera_id: int | None = None
    input_plate: str | None = None
    input_zone_id: int | None = None
    input_floor_number: int | None = None


class ReportCreate(ReportBase): ...


class ReportUpdate(ReportBase): ...


class ReportInDBBase(ReportBase):
    id: int
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Report(ReportInDBBase):
    pass
