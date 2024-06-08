from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.base import EquipmentType


class Equipment(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    equipment_type: Mapped[EquipmentType] = mapped_column(
        Integer, nullable=True
    )
    tag: Mapped[str] = mapped_column(String(30), nullable=True)
    serial_number: Mapped[str] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(15), nullable=True)
    additional_data: Mapped[dict] = mapped_column(JSON, default=dict)

    parking_id: Mapped[int] = mapped_column(Integer, ForeignKey("parking.id"))
    parking = relationship("Parking")
    zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parkingzone.id"), nullable=True
    )
    zone = relationship("ParkingZone")
