from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.base_class import Base


class PlateList(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String, nullable=True, index=True)

    plate: Mapped[str] = mapped_column(String, nullable=True, index=True)

    type: Mapped[str] = mapped_column(String, nullable=True, index=True)

    vehicle_model: Mapped[str] = mapped_column(
        String, nullable=True, index=True
    )

    vehicle_color: Mapped[str] = mapped_column(
        String, nullable=True, index=True
    )

    phone_number: Mapped[str] = mapped_column(
        String, nullable=True, index=True
    )


class AuthOTP(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    phone_number: Mapped[str] = mapped_column(
        String, nullable=True, index=True
    )

    code: Mapped[int] = mapped_column(Integer, nullable=True, index=True)

    expire_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=None), nullable=True, index=True
    )

    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=True
    )
