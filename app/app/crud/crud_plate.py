from datetime import datetime, timezone
from typing import Awaitable

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.plate import Plate
from app.parking.models.equipment import Equipment
from app.schemas.plate import (
    PlateCreate,
    PlateUpdate,
    ParamsPlates,
    ReportDoor,
)
from cache.redis import redis_client
from sqlalchemy import func


class CRUDPlate(CRUDBase[Plate, PlateCreate, PlateUpdate]):
    def create(
        self,
        db: Session | AsyncSession,
        *,
        obj_in: PlateCreate | dict,
        commit: bool = True,
    ) -> Plate | Awaitable[Plate]:
        # asyncpg raises DataError for str datetime fields
        # jsonable_encoder converts datetime fields to str
        # to avoid asyncpg error pass obj_in data as a dict
        # with datetime fields with python datetime type
        obj_in_data = obj_in
        if not isinstance(obj_in, dict):
            obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        redis_client.publish(
            "plates:1", rapidjson.dumps(jsonable_encoder(db_obj))
        )
        return self._commit_refresh(db=db, db_obj=db_obj, commit=commit)

    async def find_plates(
        self, db: Session | AsyncSession, *, params: ParamsPlates
    ) -> list[Plate] | Awaitable[list[Plate]]:

        query = select(Plate)

        filters = [Plate.is_deleted == False]

        if params.input_plate is not None:
            filters.append(Plate.plate == params.input_plate)

        if params.input_camera_id is not None:
            filters.append(Plate.camera_id == params.input_camera_id)

        if params.input_time_min is not None:
            filters.append(Plate.record_time >= params.input_time_min)

        if params.input_record_id is not None:
            filters.append(Plate.record_id == params.input_record_id)

        if params.input_time_max is not None:
            filters.append(Plate.record_time <= params.input_time_max)

        if params.size is None:
            return await self._all(
                db.scalars(query.filter(*filters).offset(params.skip))
            )

        all_items_count = await self.count_by_filter(db, filters=filters)

        items = await self._all(
            db.scalars(
                query.filter(*filters).offset(params.skip).limit(params.size)
            )
        )

        return [items, all_items_count]

    async def count_entrance_exit_door(
        self, db: AsyncSession, camera_id: int
    ) -> ReportDoor:
        camera_id_obj = {camera_id}
        query = (
            select(
                # func.distinact return unique value
                func.count(Plate.camera_id).label("count")
            )
            .where(Plate.camera_id.in_(camera_id_obj))
            .group_by(Plate.camera_id)
        )

        filters = [
            Plate.is_deleted == False,
            Plate.created >= datetime.now(timezone.utc).date(),
        ]
        execute_query = await db.execute(query.filter(*filters))

        count = execute_query.scalar()

        return count


plate = CRUDPlate(Plate)
