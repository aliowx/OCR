from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User  # noqa: F401
    from .camera import Camera  # noqa: F401


class Plate(Base):
    id = Column(Integer, primary_key=True, index=True)

    ocr = Column(String, index=True)

    lpr_id = Column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
    )
    lpr = relationship("Image", foreign_keys=lpr_id)

    big_image_id = Column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
    )
    big_image = relationship("Image", foreign_keys=big_image_id)

    record_time = Column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    number_line = Column(Integer)

    floor_number = Column(Integer)
    floor_name = Column(String)

    name_parking = Column(String)

    camera_id = Column(Integer, ForeignKey("camera.id"), index=True)
    camera_plate = relationship("Camera", back_populates="parking_plate")

    record_id = Column(Integer, ForeignKey("record.id"), index=True)
    record = relationship("Record", back_populates="plates")
