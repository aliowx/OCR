from datetime import datetime


def calculate_price(
    start_time_in: datetime, end_time_in: datetime, price_in: float = 5000
) -> float:

    duration_time = convert_time_to_hour(start_time_in, end_time_in)

    price = duration_time * price_in
    
    return price


def convert_time_to_hour(start_time, end_time):
    if start_time > end_time:
        return 0
    days = 0
    time_diffrence = end_time - start_time

    # seprating day from time
    if time_diffrence.days:
        days = time_diffrence.days * 24
        time_diffrence = str(time_diffrence).split(", ")[
            1
        ]  # example 1 day, 00:00:00 -> 00:00:00
    # Calculation hours, conversion minutes and seconds to hours
    hours, minutes, seconds = map(float, str(time_diffrence).split(":"))
    hours = hours if hours > 0 else 0
    minutes = minutes / 60 if minutes > 0 else 0
    seconds = seconds / 3600 if seconds > 0 else 0
    time_diffrence = hours + minutes + seconds + days
    return round(time_diffrence, 2)
