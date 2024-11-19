from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Boolean,
    JSON,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, get_now_datetime_utc


class Event(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate: Mapped[str] = mapped_column(String, index=True)

    record_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=get_now_datetime_utc,
        index=True,
    )

    type_event: Mapped[str] = mapped_column(String, nullable=True)

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
        nullable=True,
    )
    camera = relationship("Equipment", foreign_keys=camera_id)

    record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("record.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    record = relationship("Record", back_populates="events")

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

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    user_rel = relationship("User", foreign_keys=user_id)

    invalid: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False, index=True
    )

    additional_data: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=True
    )

    direction_info: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=True
    )

    correct_ocr: Mapped[str] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index(
            "event_plate_trgm_idx",
            "plate",
            postgresql_ops={"plate": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
    )
