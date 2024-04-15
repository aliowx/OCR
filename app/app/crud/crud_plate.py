import rapidjson
from datetime import datetime
from typing import Any, Awaitable
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func
from app.crud.base import CRUDBase
from app.models.plate import Plate
from app.schemas.plate import (
    PlateCreate,
    PlateUpdate,
)
from app.core.config import settings
from cache.redis import redis_client


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

    def get_by_record(
        self,
        db: Session | AsyncSession,
        *,
        record_id: int,
        skip: int = 0,
        limit: int = 100,
        asc: bool = True,
    ) -> list[Plate] | Awaitable[list[Plate]]:
        query = (
            select(self.model)
            .filter(Plate.record_id == record_id, Plate.is_deleted == False)
            .order_by(self.model.id.asc() if asc else self.model.id.desc())
            .offset(skip)
        )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    async def find_plates(
        self,
        db: Session | AsyncSession,
        *,
        input_ocr: str = None,
        input_camera_id: int = None,
        input_time_min: datetime = None,
        input_time_max: datetime = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Plate] | Awaitable[list[Plate]]:

        query = select(Plate)

        filters = [Plate.is_deleted == False]

        if input_ocr is not None:
            filters.append(Plate.ocr.like(f"%{input_ocr}%"))

        if input_camera_id is not None:
            filters.append(Plate.camera_id == input_camera_id)

        if input_time_min is not None:
            filters.append(Plate.record_time >= input_time_min)

        if input_time_max is not None:
            filters.append(Plate.record_time <= input_time_max)

        if limit is None:
            return await self._all(
                db.scalars(query.filter(*filters).offset(skip))
            )

        all_items_count = await self.count_by_filter(db, filters=filters)

        items = await self._all(
            db.scalars(query.filter(*filters).offset(skip).limit(limit))
        )

        return [items, all_items_count]


plate = CRUDPlate(Plate)
