from sqlalchemy import JSON, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.base import EquipmentStatus, EquipmentType


class Equipment(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    equipment_type: Mapped[EquipmentType] = mapped_column(
        Integer, nullable=True
    )
    equipment_status: Mapped[EquipmentStatus] = mapped_column(
        Integer, nullable=True
    )
    serial_number: Mapped[str] = mapped_column(String(50), nullable=True)

    tag: Mapped[str] = mapped_column(String, nullable=True)

    ip_address: Mapped[str] = mapped_column(String(15), nullable=True)

    additional_data: Mapped[dict] = mapped_column(JSON, default=dict)

    image_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "image.id",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )
    image_camera = relationship("Image", foreign_keys=image_id)

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zone.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    zone = relationship("Zone", foreign_keys=zone_id)
