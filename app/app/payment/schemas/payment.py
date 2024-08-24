from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel, ConfigDict


class StatusPayment(str, Enum):
    pay = "pay"
    unsuccessful = "unsuccessful"


# Shared properties
class PaymentBase(BaseModel):
    bill_id: int | None = None
    tracking_code: str | None = None
    status: StatusPayment | None = None


# Properties to receive on item creation
class PaymentCreate(PaymentBase): ...



# Properties to receive on item update
class PaymentUpdate(BaseModel): ...


# Properties shared by models stored in DB
class PaymentInDBBase(PaymentBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Payment(PaymentInDBBase): ...


# Properties properties stored in DB
class PaymentInDB(PaymentInDBBase): ...


# class ParamsPayment(BaseModel):
#     input_plate: str | None = None
#     input_start_time: datetime | None = None
#     input_end_time: datetime | None = None
#     input_issued_by: Issued | None = None
#     size: int | None = 100
#     page: int = 1
#     asc: bool = False

#     @property
#     def skip(self) -> int:
#         skip = 0
#         if self.size is not None:
#             skip = (self.page * self.size) - self.size
#         return skip
