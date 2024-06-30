from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class PlateDetected(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate: Mapped[str] = mapped_column(String, index=True)

    record_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    type_status_parkinglot: Mapped[str] = mapped_column(String, nullable=True)

    zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parkingzone.id"), index=True, nullable=True
    )
    zone = relationship("ParkingZone", foreign_keys=zone_id)

    parkinglot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parkinglot.id"), index=True, nullable=True
    )
    parkinglot = relationship("ParkingLot", foreign_keys=parkinglot_id)

    camera_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("camera.id"), index=True
    )
    camera_plate = relationship("Camera", back_populates="parkinglot_plate")

    record_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("record.id"), index=True, nullable=True
    )
    record = relationship("Record", back_populates="plates")

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
        Integer, ForeignKey("price.id"), index=True, nullable=True
    )
    price = relationship("Price", foreign_keys=price_model_id)
