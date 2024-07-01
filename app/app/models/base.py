from enum import IntEnum

from fastapi.params import Query


class QueryParam(Query): ...


class UserType(IntEnum):
    REAL = 0
    LEGAL = 1


class ParkingPaymentType(IntEnum):
    ON_EXIT = 0
    AFTER_EXIT = 1
    BEFORE_ENTER = 2


class EquipmentType(IntEnum):
    CAMERA_ZONE = 1
    CAMERA_SPOT = 2
    ROADBLOCK = 3
    DISPLAY = 4
    ERS = 5


class EquipmentStatus(IntEnum):
    HEALTHY = 1
    BROKEN = 2
    DISCONNECTED = 3


class RuleType(IntEnum):
    BLACK_LIST = 1
    WHITE_LIST = 2


class Weekday(IntEnum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6

    @classmethod
    @property
    def str(cls) -> str:
        return str(list(cls))
