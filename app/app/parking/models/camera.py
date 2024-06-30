from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Camera(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    camera_code: Mapped[str] = mapped_column(String)

    camera_ip: Mapped[str] = mapped_column(String, nullable=True)

    location: Mapped[str] = mapped_column(String, nullable=True)

    image_main_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "image.id",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
    )

    zone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parkingzone.id", onupdate="CASCADE", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    zone = relationship("ParkingZone", foreign_keys=zone_id)

    image_parkinglot = relationship("Image", back_populates="image_parkinglot")

    parkinglot = relationship("ParkingLot", back_populates="camera_rpi")

    parkinglot_plate = relationship(
        "PlateDetected", back_populates="camera_plate"
    )
