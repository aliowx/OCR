from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Status(str, Enum):
    full = "full"
    empty = "empty"
    dissconnect = "dissconnect"
    entranceDoor = "entranceDoor"
    exitDoor = "exitDoor"


class ParkingLotBase(BaseModel):
    camera_id: Optional[int] = Field(None)
    floor_number: Optional[int] = Field(None)
    floor_name: Optional[str] = Field(None)
    name_parkinglot: Optional[str] = Field(None)
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
    zone_id: int | None = None


class ParkingLotCreate(BaseModel):
    floor_number: int = Field(...)
    floor_name: str = Field(...)
    name_parkinglot: str = Field(...)
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
    zone_id: int | None = None


class ParkingLotShowDetailByCamera(BaseModel):
    camera_id: Optional[int] = Field(None)
    floor_number: Optional[int] = Field(None)
    floor_name: Optional[str] = Field(None)
    name_parkinglot: Optional[str] = Field(None)
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


class ParkingLotCreateLineInDB(BaseModel):
    number_line: int = Field(None, ge=1)
    camera_id: int = Field(..., ge=1)
    floor_number: int = Field(...)
    floor_name: str = Field(...)
    name_parkinglot: str = Field(...)
    percent_rotation_rectangle_big: int = Field(..., le=360, ge=0)
    coordinates_rectangle_big: List[List[float]] = Field(
        None, examples=[[0.25, 0], [1, 1]]
    )
    percent_rotation_rectangle_small: int = Field(..., le=360, ge=0)
    coordinates_rectangle_small: List[List[float]] = Field(
        None, examples=[[0.25, 0], [1, 1]]
    )
    price_model_id: int = Field(None)


class ParkingLotUpdate(ParkingLotBase):
    pass


class ParkingLotInDBBase(ParkingLotBase):
    id: Optional[int] = None
    created: Optional[datetime]
    modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ParkingLotInDB(ParkingLotInDBBase):
    pass


# Properties to return to client
class ParkingLot(ParkingLotInDBBase):
    pass


class GetParkingLot(BaseModel):
    items: dict
    all_items_count: int


class ParkingLotUpdateStatus(BaseModel):
    camera_code: str = Field(...)
    number_line: int = Field(...)
    lpr_img_id: Optional[int] = Field(None)
    ocr_img_id: Optional[int] = Field(None)
    ocr: Optional[str] = Field(None)
    status: Status = Status.empty
    latest_time_modified: Optional[datetime] = None


class PriceUpdateInParkingLot(BaseModel):
    id_park: int
    price_model_id: int
