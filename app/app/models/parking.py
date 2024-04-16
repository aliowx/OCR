from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    ARRAY,
    Float,
    DateTime,
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from .camera import Camera  # noqa: F401
    from .image import Image


class Parking(Base):
    id = Column(Integer, primary_key=True, index=True)

    floor_number = Column(Integer)
    floor_name = Column(String)

    name_parking = Column(String)

    percent_rotation_rectangle_small = Column(Integer)
    percent_rotation_rectangle_big = Column(Integer)

    coordinates_rectangle_big = Column(
        ARRAY(Float), nullable=False, index=True
    )
    coordinates_rectangle_small = Column(
        ARRAY(Float), nullable=False, index=True
    )

    number_line = Column(Integer)

    status = Column(String)

    ocr = Column(String)

    latest_time_modified = Column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    camera_id = Column(Integer, ForeignKey("camera.id"), index=True)
    camera_rpi = relationship("Camera", back_populates="parking")

    ocr_img_id = Column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
    )
    ocr_img = relationship("Image", foreign_keys=ocr_img_id)

    lpr_img_id = Column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
    )
    lpr_img = relationship("Image", foreign_keys=lpr_img_id)
