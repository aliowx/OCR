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
    bill_number: int | None = None
    zone_id: int | None = None
    img_entrance_id: int | None = None
    img_exit_id: int | None = None
    rrn_number: str | None = None
    time_paid: datetime | None = None


# Properties to receive on item creation
class BillCreate(BillBase):
    record_id: int


class BillShowBykiosk(BillCreate):
    time_park_so_far: float | None = None
    record_id: int | None = None


# Properties to receive on item update
class BillUpdate(BaseModel):
    id: int
    rrn_number: str
    time_paid: datetime
    status: StatusBill


# Properties shared by models stored in DB
class BillInDBBase(BillBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Bill(BillInDBBase):
    time_park: int | None = None
    zone_name: str | None = None
    camera_entrance: str | None = None
    camera_exit: str | None = None


class BillNotAdditionalDetail(BillInDBBase): ...


# Properties properties stored in DB
class BillInDB(BillInDBBase): ...


class ParamsBill(BaseModel):
    input_plate: str | None = None
    input_start_time: datetime | None = None
    input_end_time: datetime | None = None
    input_issued_by: Issued | None = None
    input_status: StatusBill | None = None
    input_zone_id: int | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = False

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
