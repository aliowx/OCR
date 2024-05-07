from sqlalchemy.dialects.postgresql.json import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base
from sqlalchemy import Integer, String


class Price(Base):

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name_fa: Mapped[str] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)

    price_model: Mapped[dict] = mapped_column(JSON, nullable=True)
