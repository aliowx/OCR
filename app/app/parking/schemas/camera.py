from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CameraBase(BaseModel):
    is_active: Optional[bool] = True
    camera_ip: Optional[str] = None
    camera_serial: Optional[str] = None
    location: Optional[str] = None
    image_id: Optional[int] = None
    zone_id: Optional[int] = None


class CameraCreate(CameraBase):
    camera_serial: str = Field(..., min_length=1)
    camera_ip: str = Field(...)
    location: str = Field(...)
    zone_id: str = Field(...)
    is_active: bool = Field(...)


class CameraUpdate(CameraBase):
    pass


class CameraInDBBase(CameraBase):
    id: int
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Camera(CameraInDBBase):
    pass


class CameraInDB(CameraInDBBase):
    pass


class ParamsCamera(BaseModel):
    input_camera_serail: str | None = None
    input_camera_ip: str | None = None
    input_location: str | None = None
    skip: int | None = 0
    limit: int | None = 100


class GetCamera(BaseModel):
    items: List[Camera]
    all_items_count: int
