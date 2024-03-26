from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .parking import Parking
    from .parking_ocr import ParkingOCR

class Camera(Base):
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)

    camera_code = Column(String)
    camera_ip = Column(String, nullable=True, default=None)
    
    location = Column(String)
    
    parking = relationship("Parking", back_populates="camera_rpi")
    parking_ocr = relationship("ParkingOCR", back_populates="camera_ocr")