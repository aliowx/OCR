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


plate_alphabet = {
    # 10: "الف",
    # 10: "آ",
    10: "ا",
    11: "ب",
    12: "پ",
    13: "ت",
    14: "ث",
    15: "ج",
    16: "چ",
    17: "ح",
    18: "خ",
    19: "د",
    20: "ذ",
    21: "ر",
    22: "ز",
    23: "ژ",
    24: "س",
    25: "ش",
    26: "ص",
    27: "ض",
    28: "ط",
    29: "ظ",
    30: "ع",
    31: "غ",
    32: "ف",
    33: "ق",
    34: "ک",
    35: "گ",
    36: "ل",
    37: "م",
    38: "ن",
    39: "و",
    40: "ه",
    41: "ی",
    42: "معلولین",
    43: "تشریفات",
    44: "A",
    45: "B",
    46: "C",
    47: "D",
    48: "E",
    49: "F",
    50: "G",
    51: "H",
    52: "I",
    53: "J",
    54: "K",
    55: "L",
    56: "M",
    57: "N",
    58: "O",
    59: "P",
    60: "Q",
    61: "R",
    62: "S",
    63: "T",
    64: "U",
    65: "V",
    66: "W",
    67: "X",
    68: "Y",
    69: "Z",
    0: "?",
}

plate_alphabet_reverse = {v: f"{k:0>2}" for k, v in plate_alphabet.items()}
