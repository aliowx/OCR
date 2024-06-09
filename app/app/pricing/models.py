from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Price(Base):

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name_fa: Mapped[str] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    price_model: Mapped[dict] = mapped_column(JSON, nullable=True)

    parking_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parking.id"), nullable=True
    )
    parking = relationship("Parking")
