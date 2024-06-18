from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportBase(BaseModel): ...


class SearchZoneLots(BaseModel):
    skip: int = 0
    limit: int = 100


class ZoneLots(BaseModel):
    zone_name: str = None
    list_lots: list = None

class ReportCreate(ReportBase): ...


class ReportUpdate(ReportBase): ...


class ReportInDBBase(ReportBase):
    id: int
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Report(ReportInDBBase):
    pass
