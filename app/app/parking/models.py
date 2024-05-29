from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ParkingLot(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    floor_number: Mapped[int] = mapped_column(Integer)
    floor_name: Mapped[str] = mapped_column(String)

    name_parkinglot: Mapped[str] = mapped_column(String)

    percent_rotation_rectangle_small: Mapped[int] = mapped_column(
        Integer, nullable=True
    )
    percent_rotation_rectangle_big: Mapped[int] = mapped_column(
        Integer, nullable=True
    )

    coordinates_rectangle_big: Mapped[list] = mapped_column(
        ARRAY(Float), nullable=False, index=True
    )
    coordinates_rectangle_small: Mapped[list] = mapped_column(
        ARRAY(Float), nullable=False, index=True
    )

    number_line: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String, nullable=True)

    ocr: Mapped[str] = mapped_column(String, nullable=True)

    latest_time_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    camera_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("camera.id"), index=True
    )
    camera_rpi = relationship("Camera", back_populates="parkinglot")

    ocr_img_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    ocr_img = relationship("Image", foreign_keys=ocr_img_id)

    lpr_img_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    lpr_img = relationship("Image", foreign_keys=lpr_img_id)

    price_model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("price.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    price_model = relationship("Price", foreign_keys=price_model_id)


class Camera(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    camera_code: Mapped[str] = mapped_column(String)

    camera_ip: Mapped[str] = mapped_column(String, nullable=True)

    location: Mapped[str] = mapped_column(String, nullable=True)

    # TODO: rename this column
    image_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("image.id"), index=True, nullable=True
    )
    image_parkinglot = relationship("Image", back_populates="image_parkinglot")

    parkinglot = relationship("ParkingLot", back_populates="camera_rpi")

    parkinglot_plate = relationship("Plate", back_populates="camera_plate")
