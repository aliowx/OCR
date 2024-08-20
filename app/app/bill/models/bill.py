from sqlalchemy import Integer, String, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from datetime import datetime, UTC


class Bill(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate: Mapped[str] = mapped_column(String, nullable=True)

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.now(UTC).replace(tzinfo=None),
        index=True,
    )
    
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=datetime.now(UTC).replace(tzinfo=None),
        index=True,
    )

    price: Mapped[float] = mapped_column(Float, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String, nullable=True, index=True)
