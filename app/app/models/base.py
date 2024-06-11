from enum import IntEnum

from fastapi.params import Query


class UserType(IntEnum):
    REAL = 0
    LEGAL = 1


class ParkingPaymentType(IntEnum):
    ON_EXIT = 0
    AFTER_EXIT = 1
    BEFORE_ENTER = 2


class EquipmentType(IntEnum):
    CAMERA = 1
    ROADBLOCK = 2
    DISPLAY = 3
    ERS = 4


class EquipmentStatus(IntEnum):
    HEALTHY = 1
    BROKEN = 2
    DISCONNECTED = 3


class QueryParam(Query): ...
