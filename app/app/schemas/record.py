from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# Shared properties
class RecordBase(BaseModel):
    ocr: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    best_lpr_id: Optional[int] = None
    best_big_image_id: Optional[int] = None
    price_model: Optional[dict]
    score: Optional[float] = None


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
    created: Optional[datetime]
    modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Record(RecordInDBBase):
    parkinglot_time: Optional[str] = None
    parkinglot_price: Optional[float] = None
    # pass


# Properties properties stored in DB
class RecordInDB(RecordInDBBase):
    pass


class GetRecords(BaseModel):
    items: List[Record]
    all_items_count: int
