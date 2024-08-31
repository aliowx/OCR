from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from app.db.base_class import Base


class Price(Base):

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(50), nullable=True)
    name_fa: Mapped[str] = mapped_column(String(50), nullable=True)
    entrance_fee: Mapped[float] = mapped_column(Float, nullable=True)
    hourly_fee: Mapped[float] = mapped_column(Float, nullable=True)

    pricings = relationship(
        "ZonePrice", back_populates="price", lazy="immediate"
    )
