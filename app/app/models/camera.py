from sqlalchemy import Boolean, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base_class import Base


class Camera(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    camera_code: Mapped[str] = mapped_column(String)

    camera_ip: Mapped[str] = mapped_column(String, nullable=True)

    location: Mapped[str] = mapped_column(String, nullable=True)

    image_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("image.id"), index=True, nullable=True
    )
    image_parking = relationship("Image", back_populates="image_parking")

    parking = relationship("Parking", back_populates="camera_rpi")

    parking_plate = relationship("Plate", back_populates="camera_plate")
