from datetime import datetime
from typing import Optional
from enum import StrEnum
from pydantic import BaseModel, ConfigDict


class ImageBase(BaseModel):
    path_image: str | None = None
    image: Optional[str] = None
    camera_id: Optional[int] = None
    additional_data: dict | None = None


class ImageBinaryBase(ImageBase):
    image: Optional[bytes] = None


class ImageBase64Base(ImageBase):
    image: Optional[str] = None
    camera_id: Optional[int] = None


class ImageCreate(ImageBase): ...


class ImageCreateBase64(ImageBase64Base):
    image: str
    camera_id: int


class ImageCreateBinary(ImageBinaryBase):
    image: bytes


class ImageUpdateBase64(ImageBase64Base):
    pass


class ImageUpdateBinary(ImageBinaryBase):
    pass


class ImageInDBBase(ImageBase):
    id: int
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Image(ImageInDBBase):
    image: Optional[bytes] = None


class ImageDetails(ImageInDBBase):
    pass


class ImageBase64InDB(ImageBase64Base):
    id: int
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageBase64(ImageBase64Base):
    pass


class PathImageCreate(BaseModel):
    path_image: str | None = None
    camera_id: int | None = None


class ImageSaveAs(StrEnum):
    minio = "minio"
    database = "database"


class ImageInDB(ImageInDBBase):
    image: Optional[bytes] = None
