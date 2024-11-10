from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def set_utc_timezone(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        dt.astimezone(timezone.utc)
    dt = dt.replace(tzinfo=None)
    return dt


UTCDatetime = Annotated[datetime, AfterValidator(set_utc_timezone)]
