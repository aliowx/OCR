from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.db.base_class import Base


class Zone(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    tag: Mapped[str] = mapped_column(String(50), nullable=True)
    floor_number: Mapped[int] = mapped_column(Integer, nullable=True)
    floor_name: Mapped[str] = mapped_column(String, nullable=True)
    parent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("zone.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    price_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("price.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        index=True,
    )
    price_rel = relationship("Price", back_populates="price_rel_zone")
