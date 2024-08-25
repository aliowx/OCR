from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Payment(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    price: Mapped[float] = mapped_column(Float, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String, nullable=True, index=True)

    tracking_code: Mapped[int] = mapped_column(
        Integer, nullable=True, index=True
    )

    payment_bill = relationship(
        "PaymentBill", back_populates="payment_rel", lazy="immediate"
    )
