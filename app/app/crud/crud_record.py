from datetime import datetime, timedelta
from typing import Awaitable, Optional

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app import schemas
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.record import Record
from app.schemas.record import RecordCreate, RecordUpdate
from cache.redis import redis_client


class CRUDRecord(CRUDBase[Record, RecordCreate, RecordUpdate]):

    def create(
        self,
        db: AsyncSession | Session,
        *,
        obj_in: RecordCreate,
    ) -> Record:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        redis_client.publish(
            "records:1", rapidjson.dumps(jsonable_encoder(db_obj))
        )
        return self._commit_refresh(db=db, db_obj=db_obj)

    def get_by_plate(
        self,
        db: Session,
        *,
        plate: schemas.Plate,
        offset: timedelta = timedelta(
            seconds=settings.FREE_TIME_BETWEEN_RECORDS
        ),
        for_update: bool = False,
    ) -> Optional[Record]:

        q = (
            db.query(Record)
            .filter(
                (Record.ocr == plate.ocr)
                & (Record.end_time >= plate.record_time - offset)
                & (Record.start_time <= plate.record_time + offset)
            )
            .order_by(Record.end_time.desc())
        )

        if for_update:
            return q.with_for_update().first()
        else:
            return q.first()

    async def find_records(
        self,
        db: Session | AsyncSession,
        *,
        input_ocr: str = None,
        input_start_time_min: datetime = None,
        input_start_time_max: datetime = None,
        input_end_time_min: datetime = None,
        input_end_time_max: datetime = None,
        input_score: float = None,
        skip: int = 0,
        limit: int = 100,
        asc: bool = False,
    ) -> list[Record] | Awaitable[list[Record]]:

        query = select(Record)

        filters = [Record.is_deleted == False]

        if input_ocr is not None:
            filters.append(Record.ocr.like(f"%{input_ocr}%"))

        if input_start_time_min is not None:
            filters.append(Record.start_time >= input_start_time_min)

        if input_start_time_max is not None:
            filters.append(Record.start_time <= input_start_time_max)

        if input_end_time_min is not None:
            filters.append(Record.end_time >= input_end_time_min)

        if input_end_time_max is not None:
            filters.append(Record.end_time <= input_end_time_max)

        if input_score is not None:
            filters.append(Record.score >= input_score)

        if limit is None:
            return await self._all(
                db.scalars(query.filter(*filters).offset(skip))
            )

        all_items_count = await self.count_by_filter(db, filters=filters)

        items = await self._all(
            db.scalars(
                query.filter(*filters)
                .offset(skip)
                .limit(limit)
                .order_by(Record.id.asc() if asc else Record.id.desc())
            )
        )
        return [items, all_items_count]


record = CRUDRecord(Record)
