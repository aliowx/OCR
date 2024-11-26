from sqlalchemy import Integer, ForeignKey, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


class Notifications(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plate_list_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("platelist.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    plate_list_rel = relationship("PlateList", foreign_keys=plate_list_id)

    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("event.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
    )
    event_rel = relationship("Event", foreign_keys=event_id)

    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, nullable=True
    )

    text: Mapped[str] = mapped_column(String, nullable=True)

    type_notice: Mapped[str] = mapped_column(String, nullable=True)
