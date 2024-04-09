from typing import Optional, List, Dict
from graphene import relay
from graphene_sqlalchemy.types import SQLAlchemyObjectType
from graphene_sqlalchemy_filter.filters import FilterSet

from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime

from app import models
from .image import ImageCreateBase64


# Shared properties
class PlateBase(BaseModel):
    ocr: Optional[str] = None

    record_time: Optional[datetime] = None

    lpr_id: Optional[int] = None
    big_image_id: Optional[int] = None
    record_id: Optional[int] = None

    camera_id: Optional[int] = Field(None, ge=1)
    line_id: int = Field(None, ge=1)


class PlateCreate(PlateBase):
    ocr: str
    record_time: datetime
    camera_id: int = Field(None, ge=1)


# plate with lpr
class PlateWithLPR(PlateCreate):
    lpr: Optional[ImageCreateBase64] = None

    @validator("lpr", always=True)
    def ensure_only_lpr_or_lpr_id(
        cls, lpr: Optional[ImageCreateBase64], values: Dict
    ):
        lpr_id = values.get("lpr_id")

        if lpr_id is not None and lpr is not None:
            raise ValueError('only one of "lpr_id" or "lpr" can be set')
        if lpr_id is None and lpr is None:
            raise ValueError('one of "lpr_id" or "lpr" needs to be set')
        return lpr


# Properties to receive on item creation all together
class PlatesToghetherCreate(BaseModel):
    plates: List[PlateWithLPR]
    big_image: Optional[ImageCreateBase64] = None

    @validator("big_image", always=True)
    def ensure_only_big_image_or_big_image_id(
        cls, big_image: Optional[ImageCreateBase64], values: Dict
    ):

        big_image_id = None
        for plates in values.get("plates"):
            if plates.big_image_id != None:
                big_image_id = plates.big_image_id

        if big_image_id is not None and big_image is not None:
            raise ValueError(
                'only one of "big_image_id" or "big_image" can be set'
            )
        if big_image_id is None and big_image is None:
            raise ValueError(
                'one of "big_image_id" or "big_image" needs to be set'
            )
        return big_image


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


class PlateSchema(SQLAlchemyObjectType):
    class Meta:
        model = models.Plate
        interfaces = (relay.Node,)


class PlateFilter(FilterSet):
    class Meta:
        model = models.Plate
        fields = {
            "id": [...],
            "ocr": [...],
            "record_time": [...],
            "lpr_id": [...],
            "big_image_id": [...],
            "record_id": [...],
            "created": [...],
            "modified": [...],
        }
