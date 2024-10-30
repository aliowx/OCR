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
    CAMERA_ENTRANCE_DOOR = 1
    CAMERA_EXIT_DOOR = 2
    SENSOR = 3
    ROADBLOCK = 4
    DISPLAY = 5
    CAMERA_DIRECTION_EXIT = 6
    CAMERA_DIRECTION_ENTRANCE = 7
    KIOSK = 8
    PAYMENT_DEVICE = 9
    REGIONAL_SWITCH = 10
    REGIONAL_COMPUTER = 11
    REGIONAL_CONTROLLER = 12
    POS = 13


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
