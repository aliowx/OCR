from datetime import datetime, UTC
from typing import Any

from persiantools.jdatetime import JalaliDate
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.sql.sqltypes import Boolean, DateTime


class Base(DeclarativeBase):
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    is_deleted = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        default=False,
        index=True,
    )

    created = mapped_column(
        DateTime(timezone=False),
        default=datetime.now(UTC).replace(tzinfo=None),
        index=True,
    )
    modified = mapped_column(
        DateTime(timezone=False),
        default=datetime.now(UTC).replace(tzinfo=None),
        index=True,
        onupdate=datetime.now(UTC).replace(tzinfo=None),
    )

    def __str__(self):
        return f"{self.__tablename__}:{self.id}"

    def __repr__(self):
        try:
            return f"{self.__class__.__name__}({self.__tablename__}:{self.id})"
        except:
            return f"Faulty-{self.__class__.__name__}"
