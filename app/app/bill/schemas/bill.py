from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel, ConfigDict
from app.payment.schemas import payment as paymentSchemas


class Issued(str, Enum):
    kiosk = "kiosk"
    exit_camera = "exit_camera"


# Shared properties
class BillBase(BaseModel):
    plate: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    price: float | None = None
    issued_by: Issued | None = None


# Properties to receive on item creation
class BillCreate(BillBase): ...


class BillShowBykiosk(BillCreate):
    time_park_so_far: float | None = None


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
    status_payment: paymentSchemas.StatusPayment | None = None


# Properties properties stored in DB
class BillInDB(BillInDBBase): ...


class ParamsBill(BaseModel):
    input_plate: str | None = None
    input_start_time: datetime | None = None
    input_end_time: datetime | None = None
    input_issued_by: Issued | None = None
    input_payment: paymentSchemas.StatusPayment | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = False

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
