from datetime import datetime
from typing import Any

from persiantools.jdatetime import JalaliDate
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.sqltypes import Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column


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

    created = mapped_column(DateTime(timezone=True), default=datetime.now, index=True)
    modified = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        index=True,
        onupdate=datetime.now,
    )

    def __str__(self):
        return f"{self.__tablename__}:{self.id}"

    def __repr__(self):
        try:
            return f"{self.__class__.__name__}({self.__tablename__}:{self.id})"
        except:
            return f"Faulty-{self.__class__.__name__}"

    @property
    def created_jalali(self) -> JalaliDate:
        created = (self.created).replace(tzinfo=None)
        return self.make_jalali(created)

    @property
    def modified_jalali(self) -> JalaliDate:
        modified = (self.modified).replace(tzinfo=None)
        return self.make_jalali(modified)

    def make_jalali(date_time: datetime) -> JalaliDate:
        utc = datetime.strptime(str(date_time), "%Y-%m-%d %H:%M:%S.%f")
        hour = "{:0>2}".format(int(utc.hour))
        minute = "{:0>2}".format(int(utc.minute))
        second = "{:0>2}".format(int(utc.second))
        time = hour + ":" + minute + ":" + second
        return JalaliDate(utc).strftime("%Y-%m-%d") + " " + time
