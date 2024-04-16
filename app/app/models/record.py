from typing import TYPE_CHECKING
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Float,
)
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User
    from .image import Image  # noqa: F401


class Record(Base):
    id = Column(Integer, primary_key=True, index=True)

    ocr = Column(String, index=True)

    start_time = Column(
        DateTime(timezone=True), default=datetime.now, index=True
    )
    end_time = Column(
        DateTime(timezone=True), default=datetime.now, index=True
    )

    score = Column(Float, nullable=True, default=None, index=True)

    plates = relationship("Plate", back_populates="record")

    best_lpr_id = Column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
    )
    best_lpr = relationship("Image", foreign_keys=best_lpr_id)

    best_big_image_id = Column(
        Integer,
        ForeignKey("image.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
    )
    best_big_image = relationship("Image", foreign_keys=best_big_image_id)
