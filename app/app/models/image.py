from sqlalchemy import Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.base_class import Base
from sqlalchemy.sql.sqltypes import LargeBinary


class Image(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    image: Mapped[str] = mapped_column(LargeBinary)

    image_parking = relationship("Camera", back_populates="image_parking")
