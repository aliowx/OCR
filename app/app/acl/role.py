from enum import auto


from app.core.enums import StrEnum


class UserRoles(StrEnum):
    SUPERADMIN = auto()
    ADMIN_EQUIPMENT = auto()
    ADMIN_USER = auto()
    ADMIN_PRICE = auto()
    ADMIN_ZONE_SPOT = auto()
    ADMIN_PLATE_RECORD = auto()
    READER_EQUIPMENT = auto()
    READER_USER = auto()
    READER_PRICE = auto()
    READER_ZONE_SPOT = auto()
    READER_PLATE_RECORD = auto()
