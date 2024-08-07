from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from app.parking.schemas import Status, ParamsCamera
from app.report.repo import (
    zonereportrepository,
    spotreportrepository,
)
from app.utils import PaginatedContent
from app.report.schemas import (
    ZoneLots,
    ReadZoneLotsParams,
    ParamsRecordMoment,
    ParamsRecordMomentFilters,
)
from app.api.services import records_services
from app import schemas, crud
from app.parking.repo import equipment_repo, zone_repo
from app.parking.schemas.equipment import ReadEquipmentsFilter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


async def report_zone(db: AsyncSession, params: ReadZoneLotsParams):

    # list all zone
    zones = await zonereportrepository.get_multi_by_filter(db, params=params)

    list_lots_zone = []
    for zone in zones:
        # list lots zone
        lots = await spotreportrepository.find_lines(
            db, params=ReadZoneLotsParams(input_zone_id=zone.id)
        )
        if lots:
            capacity_empty = capacity = len(lots)
            lots = jsonable_encoder(lots)
            for lot in lots:
                if lot["status"] == Status.full:
                    capacity_empty = capacity - 1
                records = await records_services.calculator_price(
                    db=db,
                    params=schemas.ParamsRecord(input_plate=lot["plate"]),
                )
            zone_lots = ZoneLots(
                zone_name=zone.name,
                list_lots=lots,
                record=records.items,
                capacity=capacity,
                capacity_empty=capacity_empty,
            )
            list_lots_zone.append(jsonable_encoder(zone_lots))

    if params.size is not None:  # limit
        list_lots_zone = list_lots_zone[: params.size]

    if params.page is not None:  # skip
        list_lots_zone = list_lots_zone[:: params.page]

    if params.asc:
        list_lots_zone.reverse()

    return PaginatedContent(
        data=list_lots_zone,
        total_count=len(list_lots_zone),
        size=params.size,
        page=params.page,
    )


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

    # Calculate the absolute difference in seconds
    difference = end_time - start_time

    # Calculate the percentage difference, capped at 100%
    try:
        percentage_difference = (difference / start_time) * 100

        # Cap the percentage difference to 100%
        if percentage_difference > 100:
            percentage_difference = 100

        return percentage_difference
    except ZeroDivisionError:
        return 0


async def dashboard(db: AsyncSession):
    result = {}

    date_today = datetime.now().date()

    records, total_count_record = await crud.record.find_records(
        db, input_start_create_time=date_today
    )

    result["total_park_today"] = total_count_record

    zones = await zone_repo.get_multi(db)
    records, total_count_record = await crud.record.find_records(
        db, input_status_record=schemas.StatusRecord.unfinished
    )
    capacity_total = 0
    capacity_empty = 0
    if zones:
        for zone in zones:
            capacity_total += zone.capacity if zone.capacity else 0

    result["report_capacity"] = {
        "capacity_total": capacity_total,
        "capacity_empty": (
            capacity_total - total_count_record
            if total_count_record
            else capacity_empty
        ),
        "capacity_full": total_count_record,
    }

    one_day_ago = datetime.now() - timedelta(days=1)
    one_week_ago = datetime.now() - timedelta(days=7)
    one_month_ago = datetime.now() - timedelta(days=30)
    six_month_ago = datetime.now() - timedelta(days=180)
    one_year_ago = datetime.now() - timedelta(days=365)

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

                if comparing_time == comparing_one_day_ago_pervious_day:
                    compare_avrage_one_day_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if comparing_time == comparing_one_week_ago_pervious_week:
                    compare_avrage_one_week_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if comparing_time == comparing_one_month_ago_pervious_month:
                    compare_avrage_one_month_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if (
                    comparing_time
                    == comparing_six_month_ago_pervious_six_month
                ):
                    compare_avrage_six_month_ago += (
                        compare_total_time_park / total_count_record_compare
                    )
                if comparing_time == comparing_one_year_ago_pervious_year:
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

    result["report_avrage_time"] = {
        "avrage_one_day_ago": {
            "time": round(avrage_one_day_ago, 4),
            "compare_percentage_with_pervious_day": (
                calculate_percentage(
                    compare_avrage_one_day_ago, avrage_one_day_ago
                )
            ),
        },
        "avrage_one_week_ago": {
            "time": round(avrage_one_week_ago, 4),
            "compare_percentage_with_pervious_week": calculate_percentage(
                compare_avrage_one_week_ago, avrage_one_week_ago
            ),
        },
        "avrage_one_month_ago": {
            "time": round(avrage_one_month_ago, 4),
            "compare_percentage_with_pervious_month": calculate_percentage(
                compare_avrage_one_month_ago, avrage_one_month_ago
            ),
        },
        "avrage_six_month_ago": {
            "time": round(avrage_six_month_ago, 4),
            "compare_percentage_with_pervious_six_month": calculate_percentage(
                compare_avrage_six_month_ago, avrage_six_month_ago
            ),
        },
        "avrage_one_year_ago": {
            "time": round(avrage_one_year_ago, 4),
            "compare_percentage_with_pervious_year": calculate_percentage(
                compare_avrage_one_year_ago, avrage_one_year_ago
            ),
        },
    }

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
    date_refferd = []
    for day in time_eghit_day_referred:
        start_date = day.replace(hour=0, minute=0, second=1)
        end_date = day.replace(hour=23, minute=59, second=59)

        records, total_count_record = await crud.record.find_records(
            db,
            input_status_record=schemas.StatusRecord.finished,
            input_start_create_time=start_date,
            input_end_create_time=end_date,
        )
        date_refferd.append(
            {"date": start_date.date(), "count_refferd": total_count_record}
        )
    date_refferd_cahnge = []

    date_refferd.reverse()
    for refferd in range(len(date_refferd)):

        today = date_refferd[refferd]["count_refferd"]

        yesterday = date_refferd[refferd - 1]["count_refferd"]

        # for division zero
        if yesterday != 0 and today != 0:
            percent_comparing = ((today + yesterday) / today) * 100
        else:
            percent_comparing = 0

        date_refferd_cahnge.append(
            {
                "start_date": date_refferd[refferd]["date"],
                "count_refferd": date_refferd[refferd]["count_refferd"],
                "percent": round(percent_comparing),
            }
        )
    date_refferd_cahnge.remove(date_refferd_cahnge[0])

    list_referred["comparing_today_with_yesterday_one_week"] = (
        date_refferd_cahnge
    )

    result["list_referred"] = list_referred

    max_time_park = await crud.record.max_time_record(db)

    result["list_max_time_park"] = [
        {"plate": plate, "created": created, "timr_park": time_park}
        for plate, created, time_park in max_time_park
    ]

    return PaginatedContent(data=result)


async def report_moment(db: AsyncSession):
    result = {}
    plate_group = await crud.plate.count_entrance_exit_door(db)
    for count, type_camera, zone_id in plate_group:
        result["count_entrance_exit_door"] = {
            "count": count,
            "type_camera": type_camera,
            "zone_id": zone_id,
        }

    return PaginatedContent(data=result)
