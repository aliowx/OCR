from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas, crud
from app.parking.repo import zone_repo
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.report import schemas as report_schemas


# calculate  first date month
def get_month_dates(reference_date, months_ago):
    month_dates = []

    for i in range(1, months_ago + 1):
        # Calculate the start date of the month `i` months ago
        start_date = (reference_date - relativedelta(months=i)).replace(day=1)

        # Calculate the end date of that month
        end_date = (start_date + relativedelta(months=1)).replace(
            day=1
        ) - timedelta(days=1)

        month_dates.append((start_date, end_date))

    return month_dates


def calculate_percentage(start_time, end_time):
    """Calculate the normalized percentage difference between start_time and end_time."""
    percentage_difference = 0
    # handel devision zero
    if end_time == 0:
        return percentage_difference
    # Calculate the absolute difference in seconds
    difference = start_time - end_time
    # Calculate the percentage difference, capped at 100%
    if difference == 0:
        return percentage_difference

    percentage_difference = (difference / end_time) * 100
    # Cap the percentage difference to 100%

    return round(percentage_difference)


async def capacity(db: AsyncSession):

    date_today = datetime.now().date()

    records, total_count_today_park = await crud.record.find_records(
        db, input_start_create_time=date_today
    )

    zones = await zone_repo.get_multi(db)
    records, total_count_in_parking = await crud.record.find_records(
        db, input_status_record=schemas.StatusRecord.unfinished
    )
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
        total_today_park=total_count_today_park
    )


async def average_time(db: AsyncSession):
    result = {}
    one_day_ago = datetime.now().date()
    one_week_ago = (datetime.now() - timedelta(days=7)).date()
    one_month_ago = (datetime.now() - timedelta(days=30)).date()
    six_month_ago = (datetime.now() - timedelta(days=180)).date()
    one_year_ago = (datetime.now() - timedelta(days=365)).date()

    timing_park = [
        one_day_ago,
        one_week_ago,
        one_month_ago,
        six_month_ago,
        one_year_ago,
    ]

    comparing_one_day_ago_pervious_day = one_day_ago - timedelta(days=1)
    comparing_one_week_ago_pervious_week = one_week_ago - timedelta(days=7)
    comparing_one_month_ago_pervious_month = one_month_ago - timedelta(days=30)
    comparing_six_month_ago_pervious_six_month = six_month_ago - timedelta(
        days=180
    )
    comparing_one_year_ago_pervious_year = one_year_ago - timedelta(days=365)

    comparing_time = [
        comparing_one_day_ago_pervious_day,
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
                input_status_record=schemas.StatusRecord.finished,
                input_start_create_time=compare_time,
                input_end_create_time=time_park,
            )
        )
        if records_compare:
            for record in records_compare:
                # print(record)
                # Calculation of spot time
                time_park_record_compare = str(
                    record.end_time - record.start_time
                )
                # Calculation hours, conversion minutes and seconds to hours
                hours, minutes, seconds = map(
                    float, time_park_record_compare.split(":")
                )
                hours = hours * 60 if hours > 0 else 0
                minutes = minutes if minutes > 0 else 0
                seconds = seconds / 60 if seconds > 0 else 0
                compare_total_time_park = hours + minutes + seconds
                if compare_time == comparing_one_day_ago_pervious_day:

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

    avrage_one_day_ago = 0
    avrage_one_week_ago = 0
    avrage_one_month_ago = 0
    avrage_six_month_ago = 0
    avrage_one_year_ago = 0

    for time in timing_park:
        records, total_count_record_timing = await crud.record.find_records(
            db,
            input_status_record=schemas.StatusRecord.finished,
            input_start_create_time=time,
        )
        if records:
            for record in records:
                # Calculation of spot time
                time_park_record = str(record.end_time - record.start_time)
                # Calculation hours, conversion minutes and seconds to hours
                hours, minutes, seconds = map(
                    float, time_park_record.split(":")
                )
                hours = hours * 60 if hours > 0 else 0
                minutes = minutes if minutes > 0 else 0
                seconds = seconds / 60 if seconds > 0 else 0
                total_time_park = hours + minutes + seconds
                if time == one_day_ago:
                    avrage_one_day_ago += (
                        total_time_park / total_count_record_timing
                    )
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
        avrage_one_day_ago=report_schemas.AverageTimeDetail(
            time=round(avrage_one_day_ago),
            compare=calculate_percentage(
                avrage_one_day_ago, compare_avrage_one_day_ago
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
    time_weekly_referred = [
        datetime.now() - timedelta(days=i) for i in range(1, 8)
    ]

    time_month_referred = [
        datetime.now() - timedelta(days=i) for i in range(1, 30)
    ]

    time_six_month_referred = get_month_dates(datetime.now(), 6)

    time_one_year_referred = get_month_dates(datetime.now(), 12)

    timing_referred = [
        (time_weekly_referred, "week"),
        (time_month_referred, "month"),
        (time_six_month_referred, "six_month"),
        (time_one_year_referred, "year"),
    ]

    compare_time_weekly_referred = [
        time_weekly_referred[-1] - timedelta(days=i) for i in range(1, 8)
    ]

    compare_time_month_referred = [
        time_month_referred[-1] - timedelta(days=i) for i in range(1, 30)
    ]

    compare_time_six_month_referred = get_month_dates(
        time_six_month_referred[-1][-1], 6
    )

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
                start_time = referred_timeing.date()
                end_time = (referred_timeing + timedelta(days=1)).date()
                records, total_count_record_timing = (
                    await crud.record.find_records(
                        db,
                        input_status_record=schemas.StatusRecord.finished,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred_compare[key_compare].append(
                    {
                        "start_date": start_time,
                        "end_date": end_time,
                        "count_referred": total_count_record_timing,
                    },
                )
        elif key_compare == "six_month":
            for start_time, end_time in compare_time_six_month_referred:
                records, total_count_record_timing = (
                    await crud.record.find_records(
                        db,
                        input_status_record=schemas.StatusRecord.finished,
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
                records, total_count_record_timing = (
                    await crud.record.find_records(
                        db,
                        input_status_record=schemas.StatusRecord.finished,
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
                start_time = referred_timeing.date()
                end_time = (referred_timeing + timedelta(days=1)).date()
                records, total_count_record_timing = (
                    await crud.record.find_records(
                        db,
                        input_status_record=schemas.StatusRecord.finished,
                        input_start_create_time=start_time,
                        input_end_create_time=end_time,
                    )
                )
                report_referred[key].append(
                    {
                        "start_date": start_time,
                        "end_date": end_time,
                        "count_referred": total_count_record_timing,
                    },
                )
        elif key == "six_month":
            for start_time, end_time in time_six_month_referred:
                records, total_count_record_timing = (
                    await crud.record.find_records(
                        db,
                        input_status_record=schemas.StatusRecord.finished,
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
                records, total_count_record_timing = (
                    await crud.record.find_records(
                        db,
                        input_status_record=schemas.StatusRecord.finished,
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

    list_referred["avarage_all_time_referred"] = (
        await crud.record.avarage_time_referred(db)
    )

    time_eghit_day_referred = [
        datetime.now() - timedelta(days=i) for i in range(0, 9)
    ]
    date_referred = []
    for day in time_eghit_day_referred:
        start_date = day.replace(hour=0, minute=0, second=1)
        end_date = day.replace(hour=23, minute=59, second=59)

        records, total_count_record = await crud.record.find_records(
            db,
            input_status_record=schemas.StatusRecord.finished,
            input_start_create_time=start_date,
            input_end_create_time=end_date,
        )
        date_referred.append(
            {"date": start_date.date(), "count_referred": total_count_record}
        )
    date_referred_cahnge = []

    date_referred.reverse()
    for referred in range(len(date_referred)):

        today = date_referred[referred]["count_referred"]

        yesterday = date_referred[referred - 1]["count_referred"]

        # for division zero
        if yesterday != 0 and today != 0:
            percent_comparing = ((today - yesterday) / yesterday) * 100
        else:
            percent_comparing = 0

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
        time=str(timedelta(seconds=time_park.seconds)),
    )


async def report_moment(db: AsyncSession):
    data = []
    plate_group = await crud.plate.count_entrance_exit_door(db)
    for count, type_camera, camera_id, camera_name in plate_group:
        data.append(
            {
                "count": count,
                "type_camera": type_camera,
                "camera_name": camera_name,
            }
        )
    return report_schemas.CountEntranceExitDoor(count_entrance_exit_door=data)
