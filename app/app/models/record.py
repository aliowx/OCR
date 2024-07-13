from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Record(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate: Mapped[str] = mapped_column(String, index=True, nullable=True)

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    score: Mapped[float] = mapped_column(
        Float, nullable=True, default=None, index=True
    )

    best_lpr_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    best_lpr_image = relationship("Image", foreign_keys=best_lpr_image_id)

    best_plate_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    best_plate_image = relationship("Image", foreign_keys=best_plate_image_id)

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

    plates = relationship("Plate", back_populates="record")

    price_model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("price.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    price_model = relationship("Price", foreign_keys=price_model_id)
