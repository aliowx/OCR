from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


class Issued(str, Enum):
    kiosk = "kiosk"
    exit_camera = "exit_camera"


class StatusBill(str, Enum):
    paid = "paid"
    unpaid = "unpaid"


# Shared properties
class BillBase(BaseModel):
    plate: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    price: float | None = None
    issued_by: Issued | None = None
    record_id: int | None = None
    status: StatusBill | None = StatusBill.unpaid


# Properties to receive on item creation
class BillCreate(BillBase):
    record_id: int


class BillShowBykiosk(BillCreate):
    time_park_so_far: float | None = None
    record_id: int | None = None


# Properties to receive on item update
class BillUpdate(BaseModel): ...


# Properties shared by models stored in DB
class BillInDBBase(BillBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Bill(BillInDBBase):
    time_park: int | None = None


# Properties properties stored in DB
class BillInDB(BillInDBBase): ...


class ParamsBill(BaseModel):
    input_plate: str | None = None
    input_start_time: datetime | None = None
    input_end_time: datetime | None = None
    input_issued_by: Issued | None = None
    input_status: StatusBill | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = False

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
