from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum
from app import schemas
from app.bill.schemas.bill import Bill


class TicketStatus(str, Enum):
    open = "open"
    close = "close"


class TicketType(str, Enum):
    free_bill = "FreeBill"
    error_ocr = "ErrorOcr"
    issue_free_bill = "IssueFreeBill"


class TicketBase(BaseModel):
    record_id: int | None = None
    bill_id: int | None = None
    correct_plate: str | None = None
    requesting_user_id: int | None = None
    verifying_user_id: int | None = None
    status: TicketStatus | None = None
    type: TicketType | None = None
    additional_data: dict | None = None


class TicketCreate(TicketBase):
    requesting_user_id: int
    status: TicketStatus = TicketStatus.open
    type: TicketType


class TicketUpdate(TicketBase):
    verifying_user_id: int


class TicketInDBBase(TicketBase):
    id: Optional[int] = None
    created: datetime | None = None
    modified: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class Ticket(TicketInDBBase):
    record: schemas.Record | None = None
    bill: Bill | None = None


class ParamsTicket(BaseModel):
    input_plate: str | None = None
    ticket_status: TicketStatus | None = None
    ticket_type: TicketType | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
