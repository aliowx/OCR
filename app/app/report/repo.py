from app.parking.models import ParkingZone, ParkingLot
from app.parking.repo import (
    ParkingZoneCreate,
    ParkingZoneUpdate,
    ParkingLotCreate,
    ParkingLotUpdate,
)
from app.crud.base import CRUDBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import exists, false, func
from typing import Awaitable
from app.report.schemas import ReadZoneLotsParams


class ParkingZoneReportRepository(
    CRUDBase[ParkingZone, ParkingZoneCreate, ParkingZoneUpdate]
):

    async def get_multi_by_filter(
        self, db: AsyncSession, *, params: ReadZoneLotsParams
    ) -> list[ParkingZone] | Awaitable[list[ParkingZone]]:

        query = select(ParkingZone)

        filters = [ParkingZone.is_deleted == false()]

        if params.input_name_zone is not None:
            filters.append(ParkingZone.name == params.input_name_zone)
        if params.input_name_sub_zone is not None:
            filters.append(
                ParkingZone.name == params.input_name_sub_zone
                and ParkingZone.parent_id is not None
            )
        if params.input_start_time is not None:
            filters.append(ParkingZone.created >= params.input_start_time)
        if params.input_end_time is not None:
            filters.append(ParkingZone.created <= params.input_end_time)

        return await self._all(db.scalars(query.filter(*filters)))


class ParkingLotReportRepository(
    CRUDBase[ParkingLot, ParkingLotCreate, ParkingLotUpdate]
):
    async def find_lines(
        self,
        db: AsyncSession,
        *,
        input_zone_id: int = None,
        params: ReadZoneLotsParams,
    ) -> list[ParkingLot] | Awaitable[list[ParkingLot]]:

        query = select(ParkingLot)

        filters = [ParkingLot.is_deleted == false()]

        if input_zone_id is not None:
            filters.append(ParkingLot.zone_id == input_zone_id)

        if params.input_floor_number is not None:
            filters.append(
                ParkingLot.floor_number == params.input_floor_number
            )
        if params.input_start_time is not None:
            filters.append(ParkingLot.created >= params.input_start_time)
        if params.input_end_time is not None:
            filters.append(ParkingLot.created <= params.input_end_time)

        return await self._all(db.scalars(query.filter(*filters)))


parkingzonereportrepository = ParkingZoneReportRepository(ParkingZone)
parkinglotreportrepository = ParkingLotReportRepository(ParkingLot)
