from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from app.core.exceptions import ServiceFailure
from app.parking.repo import parking_repo
from app.parking.schemas import Status
from app.parking.services import parkingzone as parkingzone_services
from app.report.repo import (
    parkingzonereportrepository,
    parkinglotreportrepository,
)
from app.utils import MessageCodes, PaginatedContent
from app.report.schemas import ZoneLots, ReadZoneLotsParams
from app.api.services import records_services


async def report_zone(db: AsyncSession, params: ReadZoneLotsParams):

    # list all zone
    parkingzones = await parkingzonereportrepository.get_multi_by_filter(
        db, params=params
    )

    list_lots_zone = []
    for zone in parkingzones:
        # list lots zone
        lots = await parkinglotreportrepository.find_lines(
            db, input_zone_id=zone.id, params=params
        )
        if lots:
            capacity_empty = capacity = len(lots)
            lots = jsonable_encoder(lots)
            for lot in lots:
                if lot["status"] == Status.full:
                    capacity_empty = capacity - 1
                records = await records_services.calculator_price(
                    db=db, input_ocr=lot["ocr"]
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
