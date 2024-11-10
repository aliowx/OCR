from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator
import pytz


class Issued(str, Enum):
    kiosk = "kiosk"
    exit_camera = "exit_camera"
    admin = "admin"
    entrance = "entrance"
    pos = "pos"


class StatusBill(str, Enum):
    paid = "paid"
    unpaid = "unpaid"


class BillType(str, Enum):
    system = "system"
    free = "free"
    default = "default"


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
    entrance_fee: float | None = None
    hourly_fee: float | None = None
    camera_entrance_id: int | None = None
    camera_exit_id: int | None = None
    bill_type: BillType | None = None


# Properties to receive on item creation
class BillCreate(BillBase):
    issued_by: Issued = Issued.pos
    status: StatusBill = StatusBill.unpaid


class BillShowBykiosk(BillCreate):
    time_park_so_far: float | None = None
    record_id: int | None = None


# Properties to receive on item update
class BillUpdate(BillBase):
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

    @field_validator("start_time", "end_time", "created", mode="before")
    def convert_utc_to_iran_time(cls, value):

        if value:
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            # Define Iran Standard Time timezone
            iran_timezone = pytz.timezone("Asia/Tehran")

            # If value is naive (no timezone), localize it to UTC
            if value.tzinfo is None:
                # Localize the naive datetime to UTC
                utc_time = pytz.utc.localize(value)
            else:
                # If it's already timezone aware, convert to UTC
                utc_time = value.astimezone(pytz.utc)

            # Convert to Iran Standard Time
            return utc_time.astimezone(iran_timezone)
        return value


# Properties to return to client
class Bill(BillInDBBase):
    time_park: int | None = None
    zone_name: str | None = None
    camera_entrance: str | None = None
    camera_exit: str | None = None


class BillPaidShow(BaseModel):
    plate: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    price: float | None = None
    issued_by: Issued | None = None
    status: StatusBill | None = StatusBill.paid
    bill_number: int | None = None
    img_entrance_id: int | None = None
    img_exit_id: int | None = None
    rrn_number: str | None = None
    time_paid: datetime | None = None
    entrance_fee: float | None = None
    hourly_fee: float | None = None
    bill_type: BillType | None = None
    time_park: int | None = None
    zone_name: str | None = None
    camera_entrance: str | None = None
    camera_exit: str | None = None
    id: int | None = None


class BillUnpaidShow(BaseModel):
    plate: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    price: float | None = None
    issued_by: Issued | None = None
    status: StatusBill | None = StatusBill.unpaid
    bill_number: int | None = None
    img_entrance_id: int | None = None
    img_exit_id: int | None = None
    entrance_fee: float | None = None
    hourly_fee: float | None = None
    bill_type: BillType | None = None
    time_park: int | None = None
    zone_name: str | None = None
    camera_entrance: str | None = None
    camera_exit: str | None = None
    id: int | None = None


class PlateInfo(BaseModel):
    plate: str | None = None
    phone_number: str | None = None


class billsPaidUnpaidplate(BaseModel):
    paid: list[BillPaidShow] = []
    unpaid: list[BillUnpaidShow] = []
    user_info: PlateInfo


class BillNotAdditionalDetail(BillInDBBase): ...


# Properties properties stored in DB
class BillInDB(BillInDBBase): ...


class JalaliDate(BaseModel):
    start_jalali_date: str | None = None
    end_jalali_date: str | None = None


class ParamsBill(BaseModel):
    input_plate: str | None = None
    input_start_time: datetime | None = None
    input_end_time: datetime | None = None
    input_issued_by: Issued | None = None
    input_status: StatusBill | None = None
    input_zone_id: int | None = None
    input_camera_entrance: int | None = None
    input_camera_exit: int | None = None
    input_bill_type: BillType | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = False

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
