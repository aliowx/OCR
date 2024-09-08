from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, Sequence
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, get_now_datetime_utc
from datetime import datetime


bill_number_seq = Sequence("bill_number_seq", start=1000, increment=1)


class Bill(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_number: Mapped[int] = mapped_column(
        Integer,
        server_default=bill_number_seq.next_value(),
        unique=True,
        index=True,
    )

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zone.id", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    zone_rel = relationship("Zone", foreign_keys=zone_id)

    img_entrance_id: Mapped[int] = mapped_column(Integer, nullable=True)

    img_exit_id: Mapped[int] = mapped_column(Integer, nullable=True)

    name_zone: Mapped[str] = mapped_column(String, nullable=True, index=True)

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
