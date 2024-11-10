from sqlalchemy import JSON, NUMERIC, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


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
    parking_logo_image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "image.id",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    image_logo = relationship("Image", foreign_keys=parking_logo_image_id)
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



