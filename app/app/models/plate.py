from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Plate(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    ocr: Mapped[str] = mapped_column(String, index=True)

    record_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    number_line: Mapped[int] = mapped_column(Integer)

    floor_number: Mapped[int] = mapped_column(Integer)
    floor_name: Mapped[str] = mapped_column(String)

    name_parkinglot: Mapped[str] = mapped_column(String)

    camera_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("camera.id"), index=True
    )
    camera_plate = relationship("Camera", back_populates="parkinglot_plate")

    record_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("record.id"), index=True, nullable=True
    )
    record = relationship("Record", back_populates="plates")

    lpr_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    lpr = relationship("Image", foreign_keys=lpr_id)

    big_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    big_image = relationship("Image", foreign_keys=big_image_id)

    price_model: Mapped[dict] = mapped_column(JSON, nullable=True)
