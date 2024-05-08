from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# Shared properties
class PlateBase(BaseModel):
    ocr: Optional[str] = None

    record_time: Optional[datetime] = None

    lpr_id: Optional[int] = None
    big_image_id: Optional[int] = None
    record_id: Optional[int] = None

    camera_id: Optional[int] = Field(None, ge=1)
    number_line: Optional[int] = Field(None, ge=1)

    floor_number: Optional[int] = Field(None)
    floor_name: Optional[str] = Field(None)

    name_parking: Optional[str] = Field(None)

    price_model: Optional[dict] = Field(None)

class PlateCreate(PlateBase):
    ocr: str
    record_time: datetime
    name_parking: str
    floor_number: int
    floor_name: str
    number_line: int
    camera_id: int
    lpr_id: int
    big_image_id: int
    price_model: dict


# Properties to receive on item update
class PlateUpdate(PlateBase):
    pass


# Properties shared by models stored in DB
class PlateInDBBase(PlateBase):
    id: int
    created: Optional[datetime]
    modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Plate(PlateInDBBase):
    fancy: Optional[str]


# Properties properties stored in DB
class PlateInDB(PlateInDBBase):
    pass


class GetPlates(BaseModel):
    items: List[Plate]
    all_items_count: int
