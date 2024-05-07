from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    full = "full"
    empty = "empty"
    dissconnect = "dissconnect"


class ParkingBase(BaseModel):
    camera_id: Optional[int] = Field(None)
    floor_number: Optional[int] = Field(None)
    floor_name: Optional[str] = Field(None)
    name_parking: Optional[str] = Field(None)
    coordinates_rectangles: Optional[List[Dict]] = Field(
        None,
        examples=[
            [
                {
                    "percent_rotation_rectangle_small": 90,
                    "percent_rotation_rectangle_big": 90,
                    "number_line": 1,
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "price_model_id": 1,
                }
            ]
        ],
    )
    status: Optional[Status] = Field(None)
    ocr: Optional[str] = Field(None)
    lpr_img_id: Optional[int] = Field(None)
    ocr_img_id: Optional[int] = Field(None)
    latest_time_modified: Optional[datetime] = Field(None)


class ParkingCreate(BaseModel):
    floor_number: int = Field(...)
    floor_name: str = Field(...)
    name_parking: str = Field(...)
    coordinates_rectangles: List[Dict] = Field(
        ...,
        examples=[
            [
                {
                    "percent_rotation_rectangle_small": 90,
                    "percent_rotation_rectangle_big": 90,
                    "number_line": 1,
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "price_model_id": 1,
                }
            ]
        ],
    )
    camera_id: int = Field(..., ge=1)


class ParkingShowDetailByCamera(BaseModel):
    camera_id: Optional[int] = Field(None)
    floor_number: Optional[int] = Field(None)
    floor_name: Optional[str] = Field(None)
    name_parking: Optional[str] = Field(None)
    coordinates_rectangles: Optional[List[Dict]] = Field(
        None,
        examples=[
            [
                {
                    "percent_rotation_rectangle_small": 90,
                    "percent_rotation_rectangle_big": 90,
                    "number_line": 1,
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "price_model_id": 1,
                }
            ]
        ],
    )


class ParkingCreateLineInDB(BaseModel):
    number_line: int = Field(None, ge=1)
    camera_id: int = Field(..., ge=1)
    floor_number: int = Field(...)
    floor_name: str = Field(...)
    name_parking: str = Field(...)
    percent_rotation_rectangle_big: int = Field(..., le=360, ge=0)
    coordinates_rectangle_big: List[List[float]] = Field(
        None, examples=[[0.25, 0], [1, 1]]
    )
    percent_rotation_rectangle_small: int = Field(..., le=360, ge=0)
    coordinates_rectangle_small: List[List[float]] = Field(
        None, examples=[[0.25, 0], [1, 1]]
    )
    price_model_id: int = Field(None)


class ParkingUpdate(ParkingBase):
    pass


class ParkingInDBBase(ParkingBase):
    id: Optional[int] = None
    created: Optional[datetime]
    modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ParkingInDB(ParkingInDBBase):
    pass


# Properties to return to client
class Parking(ParkingInDBBase):
    pass


class GetParking(BaseModel):
    items: dict
    all_items_count: int


class ParkingUpdateStatus(BaseModel):
    camera_code: str = Field(...)
    number_line: int = Field(...)
    lpr_img_id: int = Field(...)
    ocr_img_id: int = Field(...)
    ocr: str = Field(...)
    status: Status = Status.empty
    latest_time_modified: Optional[datetime]
