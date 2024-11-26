from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
    ARRAY,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, get_now_datetime_utc


class Record(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate: Mapped[str] = mapped_column(String, index=True, nullable=True)

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        index=True,
    )

    score: Mapped[float] = mapped_column(
        Float, nullable=True, default=None, index=True
    )

    img_entrance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    img_entrance = relationship("Image", foreign_keys=img_entrance_id)

    img_exit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    img_exit = relationship("Image", foreign_keys=img_exit_id)

    img_plate_entrance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    img_plate_entrance = relationship(
        "Image", foreign_keys=img_plate_entrance_id
    )

    img_plate_exit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    img_plate_exit = relationship("Image", foreign_keys=img_plate_exit_id)

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

    events = relationship("Event", back_populates="record")

    latest_status: Mapped[str] = mapped_column(String, nullable=True)

    camera_entrance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipment.id"),
        index=True,
        nullable=True,
    )
    camera_entrance_rel = relationship(
        "Equipment", foreign_keys=camera_entrance_id
    )

    camera_exit_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("equipment.id"),
        index=True,
        nullable=True,
    )
    camera_exit_rel = relationship("Equipment", foreign_keys=camera_exit_id)

    combined_record_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), default=list, server_default="{}"
    )

    __table_args__ = (
        Index(
            "record_plate_trgm_idx",
            "plate",
            postgresql_ops={"plate": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
    )
