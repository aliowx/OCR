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


class SpotBase(BaseModel):
    camera_id: Optional[int] = Field(None)
    name_spot: Optional[str] = Field(None)
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
                }
            ]
        ],
    )
    status: Optional[Status] = Field(None)
    plate: Optional[str] = Field(None)
    lpr_image_id: Optional[int] = Field(None)
    plate_image_id: Optional[int] = Field(None)
    latest_time_modified: Optional[datetime] = Field(None)
    zone_id: Optional[int] = Field(None)


class SpotCreate(BaseModel):
    name_spot: str
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
                }
            ]
        ],
    )
    camera_code: str 
    zone_id: int


class CoordinateSpotsByCamera(BaseModel):
    percent_rotation_rectangle_small: Optional[int]
    percent_rotation_rectangle_big: Optional[int]
    number_line: Optional[int]
    status: Optional[Status]
    lpr_image_id: Optional[int]
    plate_image_id: Optional[int]
    coordinates_rectangle_big: Optional[list[list]]
    coordinates_rectangle_small: Optional[list[list]]
    zone_id: Optional[int]
    name_spot: Optional[str]


class ReverseCoordinatesRectangles(BaseModel):
    number_line: Optional[int]
    coordinates_rectangle_big: Optional[list[list]]
    coordinates_rectangle_small: Optional[list[list]]
    percent_rotation_rectangle_small: Optional[int]
    percent_rotation_rectangle_big: Optional[int]


class SpotsByCamera(BaseModel):
    camera_id: int
    coordinates_rectangles: list[CoordinateSpotsByCamera]


class SpotShowDetailByCamera(BaseModel):
    camera_id: Optional[int] = Field(None)
    name_spot: Optional[str] = Field(None)
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
                }
            ]
        ],
    )
    zone_id: int | None = None


class SpotCreateLineInDB(BaseModel):
    number_line: int = Field(None, ge=1)
    camera_id: int = Field(..., ge=1)
    name_spot: str = Field(...)
    percent_rotation_rectangle_big: int = Field(..., le=360, ge=0)
    coordinates_rectangle_big: List[List[float]] = Field(
        None, examples=[[0.25, 0], [1, 1]]
    )
    percent_rotation_rectangle_small: int = Field(..., le=360, ge=0)
    coordinates_rectangle_small: List[List[float]] = Field(
        None, examples=[[0.25, 0], [1, 1]]
    )
    zone_id: int = Field(None)


class SpotUpdate(SpotBase):
    pass


class SpotInDBBase(SpotBase):
    id: Optional[int] = None
    created: Optional[datetime]
    modified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SpotInDB(SpotInDBBase):
    pass


# Properties to return to client
class Spot(SpotInDBBase):
    pass


class GetSpot(BaseModel):
    items: dict
    all_items_count: int



class SpotInfoCoordinate(BaseModel):
    percent_rotation_rectangle_small: int | None = None
    percent_rotation_rectangle_big: int | None = None
    number_line: int | None = None
    coordinates_rectangle_big: list | None = None
    coordinates_rectangle_small: list | None = None
    status: Status | None = None
    plate: str | None = None
    latest_time_modified: datetime | None = None
    lpr_image_id: int | None = None
    plate_image_id: int | None = None


class SpotInfo(BaseModel):
    id: int | None = None
    camera_name: str | None = None
    name_spot: str | None = None
    zone_name: str | None = None
    coordinates_rectangles: SpotInfoCoordinate | None = None
                


class SpotUpdateStatus(BaseModel):
    camera_code: str = Field(...)
    number_line: int = Field(...)
    lpr_image_id: Optional[int] = Field(None)
    plate_image_id: Optional[int] = Field(None)
    plate: Optional[str] = Field(None)
    status: Status = Status.empty
    latest_time_modified: Optional[datetime] = None



class ParamsSpotStatus(BaseModel):
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
