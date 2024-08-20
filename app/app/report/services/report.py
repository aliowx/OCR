from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud, models
from app.parking.repo import zone_repo
from datetime import datetime, timedelta, UTC
from dateutil.relativedelta import relativedelta
from app.report import schemas as report_schemas
from app.parking.repo import equipment_repo
from app.parking.schemas import ReadEquipmentsFilter


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
    days = 0
    time_diffrence = end_time - start_time

    # seprating day from time
    if time_diffrence.days:
        days = time_diffrence.days * 24 * 60
        time_diffrence = str(time_diffrence).split(", ")[
            1
        ]  # example 1 day, 00:00:00 -> 00:00:00
    # Calculation hours, conversion minutes and seconds to hours
    hours, minutes, seconds = map(float, str(time_diffrence).split(":"))
    hours = hours * 60 if hours > 0 else 0
    minutes = minutes if minutes > 0 else 0
    seconds = seconds / 60 if seconds > 0 else 0
    time_diffrence = hours + minutes + seconds + days
    return time_diffrence


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

    count_today_except_status_unfinished = (
        await crud.record.get_total_park_today_except_unfinished(db)
    )
    zones = await zone_repo.get_multi(db)
    total_count_in_parking = await crud.record.get_total_in_parking(db)
    capacity_total = 0

    if zones:
        for zone in zones:
            capacity_total += zone.capacity if zone.capacity else 0

    return report_schemas.Capacity(
        total=capacity_total,
        empty=(
            capacity_total - total_count_in_parking
            if total_count_in_parking
            else capacity_total
        ),
        full=total_count_in_parking,
        total_today_park=count_today_except_status_unfinished
        + total_count_in_parking,
    )


async def average_time(db: AsyncSession):

    today = datetime.now(UTC).replace(tzinfo=None).date()
    one_week_ago = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)
    ).date()
    one_month_ago = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
    ).date()
    six_month_ago = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(days=180)
    ).date()
    one_year_ago = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(days=365)
    ).date()

    timing_park = [
        today,
        one_week_ago,
        one_month_ago,
        six_month_ago,
        one_year_ago,
    ]

    comparing_today_pervious_day = today - timedelta(days=1)
    comparing_one_week_ago_pervious_week = one_week_ago - timedelta(days=7)
    comparing_one_month_ago_pervious_month = one_month_ago - timedelta(days=30)
    comparing_six_month_ago_pervious_six_month = six_month_ago - timedelta(
        days=180
    )
    comparing_one_year_ago_pervious_year = one_year_ago - timedelta(days=365)

    comparing_time = [
        comparing_today_pervious_day,
        comparing_one_week_ago_pervious_week,
        comparing_one_month_ago_pervious_month,
        comparing_six_month_ago_pervious_six_month,
        comparing_one_year_ago_pervious_year,
    ]

    compare_avrage_one_day_ago = 0
    compare_avrage_one_week_ago = 0
    compare_avrage_one_month_ago = 0
    compare_avrage_six_month_ago = 0
    compare_avrage_one_year_ago = 0

    for compare_time, time_park in zip(comparing_time, timing_park):
        records_compare, total_count_record_compare = (
            await crud.record.find_records(
                db,
                input_start_create_time=compare_time,
                input_end_create_time=time_park,
            )
        )
        if records_compare:
            for record in records_compare:
                # Calculation time park
                compare_total_time_park = convert_time_to_minutes(
                    record.start_time, record.end_time
                )
                if compare_time == comparing_today_pervious_day:

                    compare_avrage_one_day_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if compare_time == comparing_one_week_ago_pervious_week:

                    compare_avrage_one_week_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if compare_time == comparing_one_month_ago_pervious_month:

                    compare_avrage_one_month_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if compare_time == comparing_six_month_ago_pervious_six_month:

                    compare_avrage_six_month_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if compare_time == comparing_one_year_ago_pervious_year:

                    compare_avrage_one_year_ago += (
                        compare_total_time_park / total_count_record_compare
                    )

    avrage_today = 0
    avrage_one_week_ago = 0
    avrage_one_month_ago = 0
    avrage_six_month_ago = 0
    avrage_one_year_ago = 0

    for time in timing_park:
        records, total_count_record_timing = await crud.record.find_records(
            db,
            input_start_create_time=time,
        )
        if records:
            for record in records:
                # Calculation time park
                total_time_park = convert_time_to_minutes(
                    record.start_time, record.end_time
                )

                if time == today:
                    avrage_today += total_time_park / total_count_record_timing
                if time == one_week_ago:
                    avrage_one_week_ago += (
                        total_time_park / total_count_record_timing
                    )
                if time == one_month_ago:
                    avrage_one_month_ago += (
                        total_time_park / total_count_record_timing
                    )
                if time == six_month_ago:
                    avrage_six_month_ago += (
                        total_time_park / total_count_record_timing
                    )
                if time == one_year_ago:
                    avrage_one_year_ago += (
                        total_time_park / total_count_record_timing
                    )

    return report_schemas.AverageTime(
        avrage_all_time=await crud.record.avarage_time_referred(db),
        avrage_one_day_ago=report_schemas.AverageTimeDetail(
            time=round(avrage_today),
            compare=calculate_percentage(
                avrage_today, compare_avrage_one_day_ago
            ),
        ),
        avrage_one_week_ago=report_schemas.AverageTimeDetail(
            time=round(avrage_one_week_ago),
            compare=calculate_percentage(
                avrage_one_week_ago, compare_avrage_one_week_ago
            ),
        ),
        avrage_one_month_ago=report_schemas.AverageTimeDetail(
            time=round(avrage_one_month_ago),
            compare=calculate_percentage(
                avrage_one_month_ago, compare_avrage_one_month_ago
            ),
        ),
        avrage_six_month_ago=report_schemas.AverageTimeDetail(
            time=round(avrage_six_month_ago),
            compare=calculate_percentage(
                avrage_six_month_ago, compare_avrage_six_month_ago
            ),
        ),
        avrage_one_year_ago=report_schemas.AverageTimeDetail(
            time=round(avrage_one_year_ago),
            compare=calculate_percentage(
                avrage_one_year_ago, compare_avrage_one_year_ago
            ),
        ),
    )


async def avrage_referrd(db: AsyncSession):
    list_referred = {}

    # Counting the one week ago
    time_weekly_referred = [
        datetime.now(UTC).replace(tzinfo=None) - timedelta(days=i)
        for i in range(0, 7)
    ]
    # Counting the one month ago
    time_month_referred = [
        datetime.now(UTC).replace(tzinfo=None) - timedelta(days=i)
        for i in range(0, 30)
    ]
    # Counting the six month ago
    time_six_month_referred = get_month_dates(
        datetime.now(UTC).replace(tzinfo=None), 6
    )
    # Counting the one year ago
    time_one_year_referred = get_month_dates(
        datetime.now(UTC).replace(tzinfo=None), 12
    )

    timing_referred = [
        (time_weekly_referred, "week"),
        (time_month_referred, "month"),
        (time_six_month_referred, "six_month"),
        (time_one_year_referred, "year"),
    ]

    # Counting the first day one week ago and counting from that one week ago before
    compare_time_weekly_referred = [
        time_weekly_referred[-1] - timedelta(days=i) for i in range(0, 8)
    ]

    # Counting the first day one month ago and counting from that one month ago before
    compare_time_month_referred = [
        time_month_referred[-1] - timedelta(days=i) for i in range(0, 30)
    ]

    # Counting the first month six month ago and counting from that month to six month before
    compare_time_six_month_referred = get_month_dates(
        time_six_month_referred[-1][-1], 6
    )

    # Counting the first month one year ago and counting from that month to one year before
    compare_time_one_year_referred = get_month_dates(
        time_one_year_referred[-1][-1], 12
    )

    timing_referred_compare = [
        (compare_time_weekly_referred, "week"),
        (compare_time_month_referred, "month"),
        (compare_time_six_month_referred, "six_month"),
        (compare_time_one_year_referred, "year"),
    ]

    report_referred_compare = {
        "week": [],
        "month": [],
        "six_month": [],
        "year": [],
    }

    for referred_time_compare, key_compare in timing_referred_compare:

        if key_compare in [
            "week",
            "month",
        ]:
            for referred_timeing in referred_time_compare:
                start_time = referred_timeing.replace(
                    hour=00,
                    minute=00,
                    second=00,
                    microsecond=000000,
                )
                end_time = referred_timeing.replace(
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999,
                )
                total_count_record_timing = (
                    await crud.record.get_count_referred(
                        db,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred_compare[key_compare].append(
                    {
                        "start_date": start_time.date(),
                        "end_date": end_time.date(),
                        "count_referred": total_count_record_timing,
                    },
                )
        elif key_compare == "six_month":
            for start_time, end_time in compare_time_six_month_referred:
                total_count_record_timing = (
                    await crud.record.get_count_referred(
                        db,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred_compare[key_compare].append(
                    {
                        "start_date": start_time.date(),
                        "end_date": end_time.date(),
                        "count_referred": total_count_record_timing,
                    },
                )
        elif key_compare == "year":
            for start_time, end_time in compare_time_one_year_referred:
                total_count_record_timing = (
                    await crud.record.get_count_referred(
                        db,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred_compare[key_compare].append(
                    {
                        "start_date": start_time.date(),
                        "end_date": end_time.date(),
                        "count_referred": total_count_record_timing,
                    },
                )

    list_referred["report_referred_compare"] = report_referred_compare

    report_referred = {
        "week": [],
        "month": [],
        "six_month": [],
        "year": [],
    }
    for referred_time, key in timing_referred:

        if key in ["week", "month"]:
            for referred_timeing in referred_time:
                start_time = referred_timeing.replace(
                    hour=00,
                    minute=00,
                    second=00,
                    microsecond=000000,
                )
                end_time = referred_timeing.replace(
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999,
                )

                total_count_record_timing = (
                    await crud.record.get_count_referred(
                        db,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred[key].append(
                    {
                        "start_date": start_time.date(),
                        "end_date": end_time.date(),
                        "count_referred": total_count_record_timing,
                    },
                )
        elif key == "six_month":
            for start_time, end_time in time_six_month_referred:

                total_count_record_timing = (
                    await crud.record.get_count_referred(
                        db,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred[key].append(
                    {
                        "start_date": start_time.date(),
                        "end_date": end_time.date(),
                        "count_referred": total_count_record_timing,
                    },
                )
        elif key == "year":
            for start_time, end_time in time_one_year_referred:
                total_count_record_timing = (
                    await crud.record.get_count_referred(
                        db,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred[key].append(
                    {
                        "start_date": start_time.date(),
                        "end_date": end_time.date(),
                        "count_referred": total_count_record_timing,
                    },
                )
    list_referred["report_referred"] = report_referred

    time_eghit_day_referred = [
        datetime.now(UTC).replace(tzinfo=None) - timedelta(days=i)
        for i in range(0, 8)
    ]
    date_referred = []
    for day in time_eghit_day_referred:
        start_date = day.replace(
            hour=00,
            minute=00,
            second=00,
            microsecond=000000,
        )
        end_date = day.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
        count_record = await crud.record.get_count_referred(
            db,
            input_start_create_time=start_date,
            input_end_create_time=end_date,
        )
        date_referred.append(
            {"date": start_date.date(), "count_referred": count_record}
        )
    date_referred_cahnge = []

    date_referred.reverse()
    for referred in range(len(date_referred)):

        today = date_referred[referred]["count_referred"]

        yesterday = date_referred[referred - 1]["count_referred"]

        percent_comparing = calculate_percentage(today, yesterday)

        date_referred_cahnge.append(
            {
                "start_date": date_referred[referred]["date"],
                "count_referred": date_referred[referred]["count_referred"],
                "percent": round(percent_comparing),
            }
        )
    date_referred_cahnge.remove(date_referred_cahnge[0])

    list_referred["comparing_today_with_yesterday_one_week"] = (
        date_referred_cahnge
    )

    return report_schemas.Referred(list_referred=list_referred)


async def max_time_park(db: AsyncSession):

    time_park, plate, created = await crud.record.max_time_record(db)
    
    return report_schemas.MaxTimePark(
        plate=plate,
        created=created,
        time=str(
            timedelta(
                days=time_park.days if time_park.days else 0,
                seconds=time_park.seconds,
            )
        ),
    )


async def report_moment(db: AsyncSession):
    cameras_zone = await equipment_repo.get_entrance_exit_camera(db)

    data = []
    for camera_zone in cameras_zone:
        count = await crud.plate.count_entrance_exit_door(
            db, camera_id=camera_zone.id
        )
        if count:
            data.append(
                {
                    "count": count,
                    "type_camera": models.base.EquipmentType(
                        camera_zone.equipment_type
                    ).name,
                    "camera_name": camera_zone.serial_number,
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
                }
            )
    return report_schemas.CountEntranceExitDoor(count_entrance_exit_door=data)
