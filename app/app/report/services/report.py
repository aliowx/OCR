from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceFailure
from app.parking.repo import parking_repo
from app.parking.schemas import SetZonePriceInput
from app.parking.services import parkingzone as parkingzone_services
from app.parking.repo import parkingzone_repo, parkinglot_repo
from app.utils import MessageCodes, PaginatedContent
from app.report.schemas import ZoneLots


async def report_zone(db: AsyncSession):
    # list all zone
    parkingzones = await parkingzone_repo.get_multi(db, limit=None)

    # list lots zone
    list_lots_zone = []

    for zone in parkingzones:
        lots = await parkinglot_repo.find_lines(
            db, limit=None, input_zone_id=zone.id
        )
        if lots:
            ZoneLots.zone_name = zone.name
            ZoneLots.list_lots = lots
            list_lots_zone.append(ZoneLots)
    

    return
