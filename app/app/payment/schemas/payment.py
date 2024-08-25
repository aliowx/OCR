from datetime import datetime
from typing import List
from enum import Enum
from pydantic import BaseModel, ConfigDict


class StatusPayment(str, Enum):
    paid = "paid"
    unsuccessful = "unsuccessful"
    awaiting_payment = "awaiting_payment"


# Shared properties
class PaymentBase(BaseModel):
    price: float | None = None
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
class Payment(PaymentInDBBase):
    payment_bill: list["PaymentBill"]


# Properties properties stored in DB
class PaymentInDB(PaymentInDBBase): ...


class ParamsPayment(BaseModel):
    input_status: StatusPayment | None = None
    input_price: float | None = None
    input_tracking_code: str | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = False

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip


class PaymentBillBase(BaseModel):
    payment_id: int | None = None
    bill_id: int | None = None


class PaymentBillCreate(PaymentBillBase): ...


class PaymentBillUpdate(PaymentBillBase): ...


class PaymentBillInDBBase(PaymentBillBase):
    id: int

    created: datetime | None = None
    modified: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PaymentBill(PaymentBillInDBBase): ...


class PaymentBillInDB(PaymentBillInDBBase): ...