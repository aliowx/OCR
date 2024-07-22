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
from app.parking.repo import equipment_repo
from app.parking.schemas.equipment import ReadEquipmentsFilter


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
    # list all zone
    zones = await zonereportrepository.get_multi_by_filter(
        db, params=ReadZoneLotsParams()
    )

    result = []
    capacity = 0
    capacity_empty = 0
    for zone in zones:
        # list lots zone
        lots = await spotreportrepository.find_lines(
            db, params=ReadZoneLotsParams(input_zone_id=zone.id)
        )
        if lots:
            capacity += len(lots)
            capacity_empty += len(lots)
            for lot in lots:
                if lot.status == Status.full.value:
                    capacity_empty = capacity - 1

    result.append(
        {"full_empty_moment": {"full": capacity, "empty": capacity_empty}}
    )

    records = await records_services.calculator_price(
        db, params=schemas.ParamsRecord()
    )

    result.append({"percent_use_"})

    return PaginatedContent(
        data=result,
        total_count=0,
        size=0,
        page=0,
    )


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
