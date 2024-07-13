from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Price(Base):

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(50), nullable=True)
    name_fa: Mapped[str] = mapped_column(String(50), nullable=True)
    weekly_days: Mapped[dict] = mapped_column(JSON, nullable=True)
    entrance_fee: Mapped[int] = mapped_column(BigInteger, nullable=True)
    hourly_fee: Mapped[int] = mapped_column(BigInteger, nullable=True)
    daily_fee: Mapped[int] = mapped_column(BigInteger, nullable=True)
    penalty_fee: Mapped[int] = mapped_column(BigInteger, nullable=True)
    expiration_datetime: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, index=True
    )

    pricings = relationship(
        "ZonePrice", back_populates="price", lazy="immediate"
    )
