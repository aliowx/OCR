from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel, ConfigDict


class StatusBill(str, Enum):
    paid = "paid"
    unsuccessful = "unsuccessful"
    paying = "paying"


# Shared properties
class BillBase(BaseModel):
    plate: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    price: float | None = None
    status: StatusBill | None = None


# Properties to receive on item creation
class BillCreate(BillBase): ...


# Properties to receive on item update
class BillUpdate(BaseModel): ...


# Properties shared by models stored in DB
class BillInDBBase(BillBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Bill(BillInDBBase): ...


# Properties properties stored in DB
class BillInDB(BillInDBBase): ...


class ParamsBill(BaseModel):
    input_plate: str | None = None
    input_start_time: datetime | None = None
    input_end_time: datetime | None = None
    input_status_bill: StatusBill | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = False

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip

