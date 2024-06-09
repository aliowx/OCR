from sqlalchemy import JSON, NUMERIC, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ForeignKeyConstraint

from app.db.base_class import Base
from app.models.base import ParkingPaymentType, UserType


class Parking(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    brand_name: Mapped[str] = mapped_column(String(50), nullable=True)
    floor_count: Mapped[int] = mapped_column(Integer, nullable=True)
    area: Mapped[int] = mapped_column(Integer, nullable=True)
    location_lat: Mapped[float] = mapped_column(NUMERIC(10, 7), nullable=True)
    location_lon: Mapped[float] = mapped_column(NUMERIC(10, 7), nullable=True)
    parking_address: Mapped[str] = mapped_column(String, nullable=True)
    parking_logo_base64: Mapped[str] = mapped_column(String, nullable=True)
    owner_first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    owner_last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    owner_national_id: Mapped[str] = mapped_column(String(50), nullable=True)
    owner_postal_code: Mapped[str] = mapped_column(String(50), nullable=True)
    owner_phone_number: Mapped[str] = mapped_column(String(50), nullable=True)
    owner_email: Mapped[str] = mapped_column(String(50), nullable=True)
    owner_sheba_number: Mapped[str] = mapped_column(String(50), nullable=True)
    owner_address: Mapped[str] = mapped_column(String, nullable=True)
    owner_type: Mapped[UserType] = mapped_column(Integer, nullable=True)
    payment_type: Mapped[ParkingPaymentType] = mapped_column(
        Integer, nullable=True
    )
    beneficiary_data: Mapped[dict] = mapped_column(JSON, default=dict)


class ParkingZone(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    tag: Mapped[str] = mapped_column(String(50), nullable=True)
    parking_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking.id"))
    parent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parkingzone.id"), nullable=True
    )
    parent = relationship(
        "ParkingZone",
        remote_side=[id],
        lazy="selectin",
        back_populates="children",
    )
    children = relationship(
        "ParkingZone", back_populates="parent", lazy="immediate"
    )
    pricings = relationship(
        "ParkingZonePrice", back_populates="zone", lazy="immediate"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["parent_id"],
            ["parkingzone.id"],
            deferrable=True,
            initially="DEFERRED",
        ),
    )


class ParkingZonePrice(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parkingzone.id"), nullable=True
    )
    zone = relationship("ParkingZone", back_populates="pricings")
    price_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("price.id"),
        nullable=True,
    )
    price = relationship("Price")
