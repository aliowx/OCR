from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


# Shared properties
class RecordBase(BaseModel):
    ocr: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    best_lpr_id: int | None = None
    best_big_image_id: int | None = None
    price_model: dict | None = None
    score: float | None = None


# Properties to receive on item creation
class RecordCreate(RecordBase):
    ocr: str
    start_time: datetime
    end_time: datetime
    price_model: dict


# Properties to receive on item update
class RecordUpdate(RecordBase):
    pass


# Properties shared by models stored in DB
class RecordInDBBase(RecordBase):
    id: int
    created: datetime | None
    modified: datetime | None

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Record(RecordInDBBase):
    parkinglot_time: str | None = None
    parkinglot_price: float | None = None


# Properties properties stored in DB
class RecordInDB(RecordInDBBase):
    pass


class GetRecords(BaseModel):
    items: List[Record]
    all_items_count: int
