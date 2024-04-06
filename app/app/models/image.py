from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.sql.sqltypes import LargeBinary
from sqlalchemy.sql.schema import Index

if TYPE_CHECKING:
    from .parking import Parking


class Image(Base):
    id = Column(Integer, primary_key=True)

    image = Column(LargeBinary)

    image_parking = relationship("Camera", back_populates="image_parking")
