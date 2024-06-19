from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ImageBase(BaseModel):
    pass


class ImageBinaryBase(ImageBase):
    image: Optional[bytes] = None


class ImageBase64Base(ImageBase):
    image: Optional[str] = None


class ImageCreateBase64(ImageBase64Base):
    image: str


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


class ImageInDB(ImageInDBBase):
    image: Optional[bytes] = None
