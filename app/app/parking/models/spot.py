from datetime import datetime, timezone

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Spot(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name_spot: Mapped[str] = mapped_column(String, nullable=True)

    percent_rotation_rectangle_small: Mapped[int] = mapped_column(
        Integer, nullable=True
    )
    percent_rotation_rectangle_big: Mapped[int] = mapped_column(
        Integer, nullable=True
    )

    coordinates_rectangle_big: Mapped[list] = mapped_column(
        ARRAY(Float), nullable=True, index=True
    )
    coordinates_rectangle_small: Mapped[list] = mapped_column(
        ARRAY(Float), nullable=True, index=True
    )

    number_spot: Mapped[int] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String, nullable=True)

    plate: Mapped[str] = mapped_column(String, nullable=True)

    latest_time_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.now(timezone.utc),
        index=True,
    )

    camera_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipment.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    camera = relationship("Equipment", foreign_keys=camera_id)

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

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zone.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    zone = relationship("Zone")
