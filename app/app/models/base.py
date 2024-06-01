from enum import IntEnum


class UserType(IntEnum):
    REAL = 0
    LEGAL = 1


class ParkingPaymentType(IntEnum):
    ON_EXIT = 0
    AFTER_EXIT = 1
    BEFORE_ENTER = 2
