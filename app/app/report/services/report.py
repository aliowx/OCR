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


async def dashboard(db: AsyncSession):
    result = []
    zones = await zone_repo.get_multi(db)
    records, total_count_record = await crud.record.find_records(
        db, input_status_record=schemas.StatusRecord.unfinished
    )
    print(total_count_record)
    capacity_total = 0
    capacity_empty = 0
    if zones:
        for zone in zones:
            capacity_total += zone.capacity

    result.append(
        {
            "report-capacity": {
                "capacity_total": capacity_total,
                "capacity_empty": (
                    capacity_total - total_count_record
                    if total_count_record
                    else capacity_empty
                ),
                "capacity_full": total_count_record,
            }
        }
    )
    one_day_ago = datetime.now() - timedelta(days=1)
    one_week_ago = datetime.now() - timedelta(days=7)
    one_month_ago = datetime.now() - timedelta(days=30)
    six_month_ago = datetime.now() - timedelta(days=180)
    one_year_ago = datetime.now() - timedelta(days=365)

    timing = [
        one_day_ago,
        one_week_ago,
        one_month_ago,
        six_month_ago,
        one_year_ago,
    ]
    avrage_one_day_ago = 0
    avrage_one_week_ago = 0
    avrage_one_month_ago = 0
    avrage_six_month_ago = 0
    avrage_one_year_ago = 0
    for time in timing:
        print(datetime.now())
        print("hello", time)
        records, total_count_record_timing = await crud.record.find_records(
            db,
            input_status_record=schemas.StatusRecord.finished,
            input_create_time=time,
        )
        if records:
            for record in records:
                # Calculation of spot time
                time_park_record = str(record.end_time - record.start_time)
                # Calculation hours, conversion minutes and seconds to hours
                hours, minutes, seconds = map(
                    float, time_park_record.split(":")
                )
                minutes = minutes / 60 if minutes > 0 else 0
                seconds = seconds / 3600 if seconds > 0 else 0
                total_time_park = hours + minutes + seconds
                print(total_time_park)
                if time == one_day_ago:
                    print("one",record)
                    avrage_one_day_ago += (
                        total_time_park / total_count_record_timing
                    )
                if time == one_week_ago:
                    print("week",record)
                    avrage_one_week_ago += (
                        total_time_park / total_count_record_timing
                    )
                if time == one_month_ago:
                    print("month",record)
                    avrage_one_month_ago += (
                        total_time_park / total_count_record_timing
                    )
                if time == six_month_ago:
                    print("six",record)
                    avrage_six_month_ago += (
                        total_time_park / total_count_record_timing
                    )
                if time == one_year_ago:
                    print("plate",record)
                    avrage_one_year_ago += (
                        total_time_park / total_count_record_timing
                    )

    result.append(
        {
            "report_avrage_time": {
                "avrage_one_day_ago": avrage_one_day_ago,
                "avrage_one_week_ago": avrage_one_week_ago,
                "avrage_one_month_ago": avrage_one_month_ago,
                "avrage_six_month_ago": avrage_six_month_ago,
                "avrage_one_year_ago": avrage_one_year_ago,
            }
        }
    )
    return PaginatedContent(data=result)


async def report_moment(db: AsyncSession, params: ParamsRecordMoment):
    camera = None
    result_moment = []
    # search by camera
    if params.input_camera_serial is not None:
        camera = await equipment_repo.one_equipment(
            db, serial_number=params.input_camera_serial
        )
    # search in zone
    if (
        params.input_name_zone
        or params.input_floor_number
        or params.input_name_sub_zone
    ):
        zones = await zonereportrepository.get_multi_by_filter(
            db,
            params=ReadZoneLotsParams(
                input_name_sub_zone=params.input_name_sub_zone,
                input_floor_number=params.input_floor_number,
                input_name_zone=params.input_name_zone,
            ),
        )

        for zone in zones:
            lots = await spotreportrepository.find_lines_moment(
                db,
                params=ParamsRecordMomentFilters(
                    input_camera_id=camera, input_zone_id=zone.id
                ),
            )
    # list all lots
    else:
        lots = await spotreportrepository.find_lines_moment(
            db, params=ParamsRecordMomentFilters(input_camera_id=camera)
        )
    # set camera_code in dict lot
    if lots:
        for lot in lots:
            camera_code = await equipment_repo.get(db, id=lot.camera_id)
            lot = jsonable_encoder(lot)
            lot.update({"camera_code": camera_code.camera_code})
            result_moment.append(lot)

    if params.size is not None:  # limit
        result_moment = result_moment[: params.size]

    if params.page is not None:  # skip
        result_moment = result_moment[:: params.page]

    if params.asc:
        result_moment.reverse()

    return PaginatedContent(
        data=result_moment,
        total_count=len(result_moment),
        size=params.size,
        page=params.page,
    )
