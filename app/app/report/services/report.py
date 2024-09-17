from sqlalchemy.ext.asyncio import AsyncSession
from app.bill.repo import bill_repo
from app.bill.schemas import bill as billSchemas
from app import schemas, crud, models
from app.parking.repo import zone_repo
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta
from app.report import schemas as report_schemas
from app.parking.repo import equipment_repo, zone_repo
from app.parking.services import zone as zone_services


# calculate  first date month
def get_month_dates(reference_date, months_ago):
    month_dates = []

    for i in range(0, months_ago):
        # Calculate the start date of the month `i` months ago
        start_date = (reference_date - relativedelta(months=i)).replace(day=1)

        # Calculate the end date of that month
        end_date = (start_date + relativedelta(months=1)).replace(
            day=1
        ) - timedelta(days=1)

        month_dates.append((start_date, end_date))

    return month_dates


# convert day, hour, seconed to minute
def convert_time_to_minutes(start_time, end_time):
    if start_time > end_time:
        return 0
    day = 0
    time_diffrence = end_time - start_time

    # seprating day from time
    if time_diffrence.days:
        day = time_diffrence.days * 24 * 60
        time_diffrence = str(time_diffrence).split(", ")[
            1
        ]  # example 1 day, 00:00:00 -> 00:00:00
    # Calculation hours, conversion minutes and seconds to hours
    hours, minutes, seconds = map(float, str(time_diffrence).split(":"))
    hours = hours * 60 if hours > 0 else 0
    minutes = minutes if minutes > 0 else 0
    seconds = seconds / 60 if seconds > 0 else 0
    time_diffrence = hours + minutes + seconds + day
    return time_diffrence


def convert_time_to_minute(time: datetime):
    minute = 0
    # seprating day from time
    if time.days:
        minute = time.days * 24 * 60
        time = str(time).split(", ")[1]  # example 1 day, 00:00:00 -> 00:00:00
    # Calculation hours, conversion minutes and seconds to hours
    hours, minutes, seconds = map(float, str(time).split(":"))
    total_minute = (hours * 60) + (minutes + minute) + (seconds / 60)
    return round(total_minute)


def calculate_percentage(start_time, end_time):
    """Calculate the normalized percentage difference between start_time and end_time."""
    percentage_difference = 0
    # handel devision zero
    if end_time == 0:
        if start_time == 0:
            return percentage_difference
        return -100
    # Calculate the absolute difference in seconds
    difference = start_time - end_time
    if difference == 0:
        return percentage_difference

    # Calculate the percentage difference, capped at 100%
    percentage_difference = (difference / end_time) * 100

    return round(percentage_difference)


async def capacity(db: AsyncSession):
    start_today = datetime.now(UTC).replace(
        tzinfo=None, hour=0, minute=0, second=0, microsecond=0
    )
    end_today = datetime.now(UTC).replace(
        tzinfo=None, hour=23, minute=59, second=59, microsecond=9999
    )
    count_referred = await crud.record.get_count_referred(
        db,
        input_start_create_time=start_today,
        input_end_create_time=end_today,
    )
    count_today_except_status_unfinished = (
        await crud.record.get_total_park_today_except_unfinished(db)
    )

    total_amount_bill = await bill_repo.get_total_amount_bill(db)

    avg_time_park = await crud.record.get_avg_time_park(
        db, start_time_in=start_today, end_time_in=end_today
    )

    capacity_zones, count_zone = await zone_repo.get_capacity_count_zone(db)

    total_count_in_parking = await crud.record.get_total_in_parking(db)
    empty = 0

    if total_count_in_parking:
        empty = capacity_zones - total_count_in_parking
        if empty < 0:
            empty = 0
    else:
        empty = capacity_zones
    return report_schemas.Capacity(
        total=capacity_zones,
        empty=empty,
        full=total_count_in_parking,
        total_today_park=count_today_except_status_unfinished
        + total_count_in_parking,
        count_referred=count_referred,
        total_amount_bill=total_amount_bill,
        avg_minute_park=convert_time_to_minute(avg_time_park),
        len_zone=count_zone,
    )


async def report_zone(db: AsyncSession):
    start_today = datetime.now(UTC).replace(
        tzinfo=None, hour=0, minute=0, second=0, microsecond=0
    )
    end_today = datetime.now(UTC).replace(
        tzinfo=None, hour=23, minute=59, second=59, microsecond=9999
    )
    zones = await zone_repo.get_multi(db, limit=None)
    for zone in zones:
        zone_id = {zone.id}
        zone = await zone_services.set_children_ancestors_capacity(db, zone)
        zone.total_referred = (
            await crud.record.get_today_count_referred_by_zone(
                db,
                zone_id=zone.id,
                start_time_in=start_today,
                end_time_in=end_today,
            )
        )
        av_time = await crud.record.get_avg_time_park(
            db,
            zone_id_in=zone.id,
            start_time_in=start_today,
            end_time_in=end_today,
        )

        zone.avrage_stop_minute_today = round(av_time.total_seconds() / 60)

        total_price, total_income = await bill_repo.get_price_income(
            db,
            zone_id=zone_id,
            start_time_in=start_today,
            end_time_in=end_today,
        )

        zone.avrage_amount_bill_today = round(total_price)
        zone.income_today_parking = round(total_income)
        zone.pricings = []
        zone.ancestors = []
        zone.children = []
        zone.rules = []

    return zones


async def park_time(
    db: AsyncSession,
    *,
    start_time_in: datetime,
    end_time_in: datetime,
):
    list_avg_zone_time_park = []
    convert_to_minute_time_park = 0
    total_avrage_park_time = await crud.record.get_avg_time_park(
        db,
        start_time_in=start_time_in,
        end_time_in=end_time_in,
    )
    zones = await zone_repo.get_multi(db, limit=None)
    for zone in zones:
        avrage_park_time = await crud.record.get_avg_time_park(
            db,
            zone_id=zone.id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
        if avrage_park_time:
            convert_to_minute_time_park = round(
                avrage_park_time.total_seconds() / 60
            )
        list_avg_zone_time_park.append(
            {
                "zone_name": zone.name,
                "avg_time_park": convert_to_minute_time_park,
            }
        )
    list_avg_zone_time_park.append(
        {
            "avg_total_time_park": round(
                total_avrage_park_time.total_seconds() / 60
            )
        }
    )

    return list_avg_zone_time_park


# Helper function to get the last day of a given month
def last_day_of_month(date: datetime):
    next_month = date.replace(day=28) + timedelta(
        days=4
    )  # this will be in the next month
    return next_month - timedelta(days=next_month.day)


def get_month_range(start_date: datetime, end_date: datetime):

    # List to store the month ranges
    month_ranges = []

    # Start iterating from the first month
    current_start = start_date.replace(day=1)

    # Loop through each month until the end_date
    while current_start <= end_date:
        current_end = last_day_of_month(current_start)
        if current_end > end_date:
            current_end = end_date

        month_ranges.append((current_start, current_end))

        # Move to the next month
        next_month = current_start + timedelta(days=31)
        current_start = next_month.replace(day=1)

    return month_ranges


def get_year_range(start_date: datetime, end_date: datetime):

    start_year = start_date.year
    end_year = end_date.year

    return [
        datetime(year, 1, 1).date() for year in range(start_year, end_year + 1)
    ]


def create_ranges_date(
    end_date: datetime, start_date: datetime, timing: report_schemas.Timing
):

    start_date = start_date.date()
    end_date = end_date.date()

    ranges = []
    current_date = start_date
    while current_date <= end_date:
        # Create a range
        start_time = current_date
        if timing == report_schemas.Timing.day:
            current_date += timedelta(days=1)
            ranges.append({"time": start_time, "count": 0})

        if timing == report_schemas.Timing.week:
            ranges.append({"time": start_time, "count": 0})
            start_time = current_date + timedelta(days=7)
            current_date += timedelta(days=7)

        if timing == report_schemas.Timing.month:
            range_month = get_month_range(start_date, end_date)
            for start, end in range_month:
                ranges.append({"time": start, "count": 0})
            return ranges

        if timing == report_schemas.Timing.year:
            years = get_year_range(start_date, end_date)
            for year in years:
                ranges.append({"time": year, "count": 0})
            return ranges

    return ranges


async def get_count_referred(
    db: AsyncSession,
    start_time_in: datetime,
    end_time_in: datetime,
    timing: report_schemas.Timing,
    zone_id: int | None = None,
) -> list:

    range_date = create_ranges_date(
        start_date=start_time_in, end_date=end_time_in, timing=timing
    )

    count_record = await crud.record.get_count_referred_by_timing(
        db,
        input_start_create_time=start_time_in,
        input_end_create_time=end_time_in,
        timing=(
            timing
            if timing != report_schemas.Timing.week
            else report_schemas.Timing.day
        ),
        zone_id=zone_id,
    )
    convert_to_dict_record = {
        time.date(): count for time, count in count_record
    }
    for item in range_date:
        if timing == report_schemas.Timing.day:
            if item["time"] in convert_to_dict_record:
                item["count"] = convert_to_dict_record[item["time"]]
        if timing == report_schemas.Timing.week:
            # For weekly grouping, sum over a 7-day period
            start_date = item[
                "time"
            ]  # Assuming `item["time"]` is the start of the week
            end_date = start_date + timedelta(days=7)
            week_count = 0

            # Iterate through each day in the 7-day period and sum up the count
            current_date = start_date
            while current_date < end_date:
                if current_date in convert_to_dict_record:
                    week_count += convert_to_dict_record[current_date]
                current_date += timedelta(days=1)
            item.update({"end_date": end_date})
            item["count"] = week_count
        if timing == report_schemas.Timing.month:
            if item["time"] in convert_to_dict_record:
                item["count"] = convert_to_dict_record[item["time"]]
                item.update({"end_time": last_day_of_month(item["time"])})
        if timing == report_schemas.Timing.year:
            if item["time"] in convert_to_dict_record:
                item["count"] = convert_to_dict_record[item["time"]]
        item["start_time"] = item.pop("time")

    return range_date


async def get_count_referred_by_zone(
    db: AsyncSession,
    start_time_in: datetime,
    end_time_in: datetime,
    timing: report_schemas.Timing,
    zone_id: int | None = None,
) -> list:

    if zone_id:
        return await get_count_referred(
            db,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            timing=timing,
            zone_id=zone_id,
        )
    list_zone = []
    if zone_id is None:
        zones_ids = await zone_repo.get_multi(db, limit=None)
        for zone in zones_ids:
            zone_data = await get_count_referred(
                db,
                start_time_in=start_time_in,
                end_time_in=end_time_in,
                timing=timing,
                zone_id=zone.id,
            )
            list_zone.append({"zone_name": zone.name, "data": zone_data})
    return list_zone


async def count_entrance_exit_zone(
    db: AsyncSession,
    zone_id: int = None,
    start_time_in: datetime | None = None,
    end_time_in: datetime | None = None,
):

    cameras_zones = await equipment_repo.get_entrance_exit_camera(
        db, zone_id=zone_id
    )
    data = []
    for camera_zone, zone in cameras_zones:
        count = await crud.event.count_entrance_exit_door(
            db,
            camera_id=camera_zone.id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
        if count:
            data.append(
                {
                    "count": count,
                    "type_camera": models.base.EquipmentType(
                        camera_zone.equipment_type
                    ).name,
                    "camera_name": camera_zone.serial_number,
                    "zone_name": zone.name,
                }
            )
        else:
            data.append(
                {
                    "count": 0,
                    "type_camera": models.base.EquipmentType(
                        camera_zone.equipment_type
                    ).name,
                    "camera_name": camera_zone.serial_number,
                    "zone_name": zone.name,
                }
            )
    return report_schemas.CountEntranceExitDoor(count_entrance_exit_door=data)


async def report_bill(
    db: AsyncSession,
    *,
    zone_id: int,
    start_time_in: datetime,
    end_time_in: datetime,
):

    total_bills, bills_paid, bills_unpaid = (
        await bill_repo.get_total_price_count(
            db,
            zone_id=zone_id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
    )

    return {
        "total_bills": {
            "price": total_bills[0],
            "count": total_bills[1],
        },
        "bills_paid": {
            "price": bills_paid[0],
            "count": bills_paid[1],
        },
        "bills_unpaid": {
            "price": bills_unpaid[0],
            "count": bills_unpaid[1],
        },
    }


async def report_bill_by_timing(
    db: AsyncSession,
    *,
    timing: report_schemas.Timing = report_schemas.Timing.day,
    zone_id: int | None = None,
    start_time_in: datetime,
    end_time_in: datetime,
):
    range_dates = create_ranges_date(
        start_date=start_time_in, end_date=end_time_in, timing=timing
    )

    total_bills = await bill_repo.get_total_price_by_timing(
        db,
        timing=(
            timing
            if timing != report_schemas.Timing.week
            else report_schemas.Timing.day
        ),
        zone_id=zone_id,
        start_time_in=start_time_in,
        end_time_in=end_time_in,
    )

    convert_total_bills = {date.date(): price for date, price in total_bills}

    for range_date in range_dates:
        if timing == report_schemas.Timing.day:
            if range_date["time"] in convert_total_bills:
                range_date["count"] = convert_total_bills[range_date["time"]]
        if timing == report_schemas.Timing.week:
            # For weekly grouping, sum over a 7-day period
            start_date = range_date[
                "time"
            ]  # Assuming `item["time"]` is the start of the week
            end_date = start_date + timedelta(days=7)
            week_price = 0

            # Iterate through each day in the 7-day period and sum up the count
            current_date = start_date
            while current_date < end_date:
                if current_date in convert_total_bills:
                    week_price += convert_total_bills[current_date]
                current_date += timedelta(days=1)
            range_date.update({"end_date": end_date})
            range_date["count"] = week_price
        if timing == report_schemas.Timing.month:
            if range_date["time"] in convert_total_bills:
                range_date["count"] = convert_total_bills[range_date["time"]]
                range_date.update(
                    {"end_time": last_day_of_month(range_date["time"])}
                )

        if timing == report_schemas.Timing.year:
            if range_date["time"] in convert_total_bills:
                range_date["count"] = convert_total_bills[range_date["time"]]

        range_date["start_time"] = range_date.pop("time")
        range_date["price"] = range_date.pop("count")

    return range_dates
