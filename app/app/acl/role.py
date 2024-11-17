from enum import auto


from app.core.enums import StrEnum


class UserRoles(StrEnum):
    ADMINISTRATOR = auto()
    PARKING_MANAGER = auto()
    TECHNICAL_SUPPORT = auto()
    OPERATIONAL_STAFF = auto()
    REPORTING_ANALYSIS = auto()
    SECURITY_STAFF = auto()
    EXIT_GATE_DOOR = auto()
    APP_IRANMALL = auto()
    ITOLL = auto()
    