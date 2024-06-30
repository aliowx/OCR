from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class ParkingLot(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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

    plate: Mapped[str] = mapped_column(String, nullable=True)

    latest_time_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    camera_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("camera.id"), index=True
    )
    camera_rpi = relationship("Camera", back_populates="parkinglot")

    plate_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    plate_image = relationship("Image", foreign_keys=plate_image_id)

    lpr_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    lpr_image = relationship("Image", foreign_keys=lpr_image_id)

    price_model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("price.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    price_model = relationship("Price", foreign_keys=price_model_id)

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parkingzone.id", ondelete="SET NULL"),
        nullable=True,
    )
    zone = relationship("ParkingZone")
