""" Message codes for api responses """

from app.core.middleware.get_accept_language_middleware import (
    get_accept_language,
)


def parseAcceptLanguage(acceptLanguage: str):
    language_codes = []
    for language in acceptLanguage.split(","):
        language = language.split(";", 1)[0]
        language = language.split("-", 1)[0]
        language = language.strip()
        language_codes.append(language)
    return language_codes


class MessageCodes:
    @classmethod
    def get_message(cls, message_code: int) -> str:
        parsed_accept_languages = parseAcceptLanguage(get_accept_language())

        for accept_language in parsed_accept_languages:
            match accept_language:
                case "fa":
                    return cls.persian_message_names[message_code]
                case "en":
                    return cls.english_messages_names[message_code]

        return cls.persian_message_names[message_code]

    # main codes start from 0
    successful_operation = 0
    internal_error = 1
    not_found = 2
    bad_request = 3
    input_error = 4
    operation_failed = 5
    forbidden = 6
    incorrect_username_or_password = 7
    duplicate_zone_name = 8
    duplicate_ip_address = 9
    duplicate_serial_number = 10
    duplicate_zone_pricing = 11
    duplicate_name = 12

    english_messages_names = {
        0: "Successful Operation",
        1: "Internal Error",
        2: "Not Found",
        3: "Bad Request",
        4: "Input Error",
        5: "Operation Failed",
        6: "Forbidden",
        7: "Incorrect username or password",
        8: "Duplicate zone name",
        9: "Duplicate ip address",
        10: "Duplicate serial number",
        11: "Duplicate zone pricing",
        12: "Duplicate name",
    }

    persian_message_names = {
        0: "عملیات موفق",
        1: "خطای داخلی",
        2: "پیدا نشد",
        3: "درخواست نا‌معتبر",
        4: "ورودی نامعتبر",
        5: "عملیات ناموفق",
        6: "دسترسی غیرمجاز",
        7: "نام کاربری یا کلمه عبور اشتباه است",
        8: "نام منطقه تکراری است",
        9: "آی‌پی تکراری است",
        10: "شماره سریال تکراری است",
        11: "قیمت‌گذاری وارد شده برای این منطقه تکراری است",
        12: "نام تکرایر است",
    }
