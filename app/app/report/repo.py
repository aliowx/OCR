from app.parking.models import Zone, Spot
from app.parking.repo import (
    ZoneCreate,
    ZoneUpdate,
    SpotCreate,
    SpotUpdate,
)
from app.crud.base import CRUDBase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import false
from typing import Awaitable
from app.report.schemas import ReadZoneLotsParams, ParamsRecordMomentFilters


class ZoneReportRepository(
    CRUDBase[Zone, ZoneCreate, ZoneUpdate]
):

    async def get_multi_by_filter(
        self, db: AsyncSession, *, params: ReadZoneLotsParams
    ) -> list[Zone] | Awaitable[list[Zone]]:

        query = select(Zone)

        filters = [Zone.is_deleted == false()]

        if params.input_name_zone is not None:
            filters.append(Zone.name == params.input_name_zone)
        if params.input_name_sub_zone is not None:
            filters.append(
                Zone.name == params.input_name_sub_zone
                and Zone.parent_id is not None
            )
        if params.input_start_time is not None:
            filters.append(Zone.created >= params.input_start_time)
        if params.input_end_time is not None:
            filters.append(Zone.created <= params.input_end_time)

        return await self._all(db.scalars(query.filter(*filters)))


class SpotReportRepository(
    CRUDBase[Spot, SpotCreate, SpotUpdate]
):
    async def find_lines(
        self,
        db: AsyncSession,
        *,
        params: ReadZoneLotsParams,
    ) -> list[Spot] | Awaitable[list[Spot]]:

        query = select(Spot)

        filters = [Spot.is_deleted == false()]

        if params.input_zone_id is not None:
            filters.append(Spot.zone_id == params.input_zone_id)

        if params.input_start_time is not None:
            filters.append(Spot.created >= params.input_start_time)
        if params.input_end_time is not None:
            filters.append(Spot.created <= params.input_end_time)

        return await self._all(db.scalars(query.filter(*filters)))

    async def find_lines_moment(
        self,
        db: AsyncSession,
        *,
        params: ParamsRecordMomentFilters,
    ) -> list[Spot] | Awaitable[list[Spot]]:

        query = select(Spot)

        filters = [Spot.is_deleted == false()]

        if params.input_camera_id is not None:
            filters.append(Spot.camera_id == params.input_camera_id)

        if params.input_zone_id is not None:
            filters.append(Spot.zone_id == params.input_zone_id)

        if params.input_plate is not None:
            filters.append(Spot.plate == params.input_plate)

        return await self._all(db.scalars(query.filter(*filters)))
    
zonereportrepository = ZoneReportRepository(Zone)
spotreportrepository = SpotReportRepository(Spot)
