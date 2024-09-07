from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, get_now_datetime_utc
from datetime import datetime


class Bill(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("record.id", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    record_rel = relationship("Record", foreign_keys=record_id)

    plate: Mapped[str] = mapped_column(String, nullable=True)

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=get_now_datetime_utc,
        index=True,
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=get_now_datetime_utc,
        index=True,
    )

    price: Mapped[float] = mapped_column(Float, nullable=True, index=True)

    issued_by: Mapped[str] = mapped_column(String, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String, nullable=True, index=True)
