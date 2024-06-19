from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import LargeBinary

from app.db.base_class import Base


class Image(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    image: Mapped[str] = mapped_column(LargeBinary)

    image_parkinglot = relationship(
        "Camera", back_populates="image_parkinglot"
    )
