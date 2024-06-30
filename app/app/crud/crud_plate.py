from datetime import datetime
from typing import Awaitable

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.plate import PlateDetected
from app.schemas.plate import PlateCreate, PlateUpdate, ParamsPlates
from cache.redis import redis_client


class CRUDPlate(CRUDBase[PlateDetected, PlateCreate, PlateUpdate]):
    def create(
        self,
        db: Session | AsyncSession,
        *,
        obj_in: PlateCreate | dict,
        commit: bool = True,
    ) -> PlateDetected | Awaitable[PlateDetected]:
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

    def get_by_record(
        self,
        db: Session | AsyncSession,
        *,
        record_id: int,
        skip: int = 0,
        limit: int = 100,
        asc: bool = True,
    ) -> list[PlateDetected] | Awaitable[list[PlateDetected]]:
        query = (
            select(self.model)
            .filter(
                PlateDetected.record_id == record_id,
                PlateDetected.is_deleted == False,
            )
            .order_by(self.model.id.asc() if asc else self.model.id.desc())
            .offset(skip)
        )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    async def find_plates(
        self, db: Session | AsyncSession, *, params: ParamsPlates
    ) -> list[PlateDetected] | Awaitable[list[PlateDetected]]:

        query = select(PlateDetected)

        filters = [PlateDetected.is_deleted == False]

        if params.input_plate is not None:
            filters.append(PlateDetected.plate == params.input_plate)

        if params.input_camera_id is not None:
            filters.append(PlateDetected.camera_id == params.input_camera_id)

        if params.input_time_min is not None:
            filters.append(PlateDetected.record_time >= params.input_time_min)

        if params.input_time_max is not None:
            filters.append(PlateDetected.record_time <= params.input_time_max)

        if params.limit is None:
            return await self._all(
                db.scalars(query.filter(*filters).offset(params.skip))
            )

        all_items_count = await self.count_by_filter(db, filters=filters)

        items = await self._all(
            db.scalars(
                query.filter(*filters).offset(params.skip).limit(params.limit)
            )
        )

        return [items, all_items_count]


plate = CRUDPlate(PlateDetected)
