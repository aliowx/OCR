from typing import Optional, List, Dict
from graphene import relay
from graphene_sqlalchemy.types import SQLAlchemyObjectType
from graphene_sqlalchemy_filter.filters import FilterSet

from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app import models


# Shared properties
class RecordBase(BaseModel):
    ocr: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    best_lpr_id: Optional[int] = None
    best_big_image_id: Optional[int] = None

    score: Optional[float] = None


# Properties to receive on item creation
class RecordCreate(RecordBase):
    ocr: str
    start_time: datetime
    end_time: datetime


# Properties to receive on check operatory update
class RecordUpdateCheckOperatory(BaseModel):
    ocr_checked: str
    additional_data: Dict


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
    fancy: Optional[str]


# Properties properties stored in DB
class RecordInDB(RecordInDBBase):
    pass


class GetRecords(BaseModel):
    items: List[Record]
    all_items_count: int


class RecordSchema(SQLAlchemyObjectType):
    class Meta:
        model = models.Record
        interfaces = (relay.Node,)


class RecordFilter(FilterSet):
    class Meta:
        model = models.Record
        fields = {
            "id": [...],
            "ocr": [...],
            "start_time": [...],
            "end_time": [...],
            "best_lpr_id": [...],
            "best_big_image_id": [...],
            "score": [...],
            "created": [...],
            "modified": [...],
        }
