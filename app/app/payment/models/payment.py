from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.bill.models import Bill
from app.db.base_class import Base, get_now_datetime_utc
from datetime import datetime, UTC


class Payment(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("bill.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bill_rel = relationship("Bill", foreign_keys=bill_id)

    status: Mapped[str] = mapped_column(String, nullable=True, index=True)

    tracking_code: Mapped[int] = mapped_column(
        Integer, nullable=True, index=True
    )
