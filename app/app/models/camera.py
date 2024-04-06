from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from .parking import Parking


class Camera(Base):
    id = Column(Integer, primary_key=True, index=True)

    is_active = Column(Boolean, default=True)

    camera_code = Column(String)

    camera_ip = Column(String, nullable=True, default=None)

    location = Column(String)

    image_id = Column(Integer, ForeignKey("image.id"), index=True)
    image_parking = relationship("Image", back_populates="image_parking")

    parking = relationship("Parking", back_populates="camera_rpi")
