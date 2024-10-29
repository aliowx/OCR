from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base, get_now_datetime_utc
from datetime import datetime 


class PlateList(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String, nullable=True, index=True)

    plate: Mapped[str] = mapped_column(
        String, nullable=True, index=True, unique=True
    )

    expire_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), index=True, default=get_now_datetime_utc
    )

    expire_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), index=True, default=get_now_datetime_utc
    )

    type: Mapped[str] = mapped_column(String, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String, nullable=True, index=True)
