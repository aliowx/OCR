from sqlalchemy import Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, get_now_datetime_utc
from datetime import datetime


class Bill(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

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

    bill_payment = relationship(
        "PaymentBill", back_populates="bill_rel", lazy="immediate"
    )


class PaymentBill(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    bill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("bill.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bill_rel = relationship("Bill", back_populates="bill_payment")

    payment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("payment.id", ondelete="SET NULL", onupdate="CASCADE"),
        index=True,
        nullable=True,
    )
    payment_rel = relationship("Payment", back_populates="payment_bill")
