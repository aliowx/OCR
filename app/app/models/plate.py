from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Plate(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate: Mapped[str] = mapped_column(String, index=True)

    record_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    type_status_spot: Mapped[str] = mapped_column(String, nullable=True)

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zone.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    zone = relationship("Zone", foreign_keys=zone_id)

    spot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("spot.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    spot = relationship("Spot", foreign_keys=spot_id)

    camera_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipment.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
    )
    camera_plate = relationship("Equipment", back_populates="spot_plate")

    record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("record.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
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
        Integer,
        ForeignKey("price.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    price = relationship("Price", foreign_keys=price_model_id)
