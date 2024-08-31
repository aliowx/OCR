from datetime import datetime, timedelta, UTC
from typing import Awaitable, Optional

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import schemas
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.record import Record
from app.schemas.record import RecordCreate, RecordUpdate
from cache.redis import redis_client
from app.schemas import RecordUpdate, StatusRecord


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

    def get_by_event(
        self,
        db: Session,
        *,
        plate: schemas.Event,
        status: StatusRecord,
        offset: timedelta = timedelta(
            seconds=settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR
        ),
        for_update: bool = False,
    ) -> Optional[Record]:

        q = (
            db.query(Record)
            .filter(
                (Record.plate == plate.plate)
                & (Record.end_time >= plate.record_time - offset)
                & (Record.start_time <= plate.record_time + offset)
                & (Record.latest_status == status)
            )
            .order_by(Record.end_time.desc())
        )

        if for_update:
            return q.with_for_update().first()
        else:
            return q.first()

    async def get_total_park_today_except_unfinished(
        self, db: Session | AsyncSession
    ):

        return await db.scalar(
            select(Record)
            .with_only_columns(func.count())
            .filter(
                (Record.latest_status != StatusRecord.unfinished.value)
                & (
                    Record.created
                    >= datetime.now(UTC).replace(tzinfo=None).date()
                ),
            )
        )

    async def get_total_in_parking(self, db: Session | AsyncSession):

        return await db.scalar(
            select(Record)
            .with_only_columns(func.count())
            .filter((Record.latest_status == StatusRecord.unfinished.value))
        )

    async def get_count_referred(
        self,
        db: Session | AsyncSession,
        *,
        input_start_create_time: datetime = None,
        input_end_create_time: datetime = None,
    ):

        query = select(Record)

        filters = [Record.is_deleted == False]

        filters.append(
            Record.created.between(
                input_start_create_time, input_end_create_time
            )
        )

        return await db.scalar(
            query.with_only_columns(func.count()).filter(*filters)
        )

    async def find_records(
        self,
        db: Session | AsyncSession,
        *,
        input_plate: str = None,
        input_zone_id: int = None,
        input_status_record: StatusRecord = None,
        input_start_create_time: datetime = None,
        input_end_create_time: datetime = None,
        input_score: float = None,
        skip: int = 0,
        limit: int | None = None,
        asc: bool = False,
    ) -> list[Record] | Awaitable[list[Record]]:

        query = select(Record)

        filters = [Record.is_deleted == False]

        if input_plate is not None:
            filters.append(Record.plate.ilike(f"%{input_plate}%"))

        if input_zone_id is not None:
            filters.append(Record.zone_id == input_zone_id)

        if input_start_create_time is not None:
            filters.append(Record.created >= input_start_create_time)

        if input_end_create_time is not None:
            filters.append(Record.created <= input_end_create_time)

        if input_status_record is not None:
            filters.append(Record.latest_status == input_status_record)

        if input_score is not None:
            filters.append(Record.score >= input_score)

        all_items_count = await self.count_by_filter(db, filters=filters)
        if limit is None:
            result = await self._all(
                db.scalars(query.filter(*filters).offset(skip))
            )

            return [result, all_items_count]
        result = await self._all(
            db.scalars(
                query.filter(*filters)
                .offset(skip)
                .limit(limit)
                .order_by(Record.id.asc() if asc else Record.id.desc())
            )
        )
        return [result, all_items_count]

    async def get_record(
        self,
        db: Session | AsyncSession,
        *,
        input_plate: str = None,
        input_status: StatusRecord = None,
    ):
        query = select(Record)

        filters = [Record.is_deleted == False]

        if input_plate is not None:
            filters.append(Record.plate == input_plate)

        if input_status is not None:
            filters.append(Record.latest_status == input_status)

        return await self._first(db.scalars(query.filter(*filters)))

    async def max_time_record(
        self, db: Session | AsyncSession
    ) -> list[Record]:

        sub_query = select(
            func.max(Record.end_time - Record.start_time)
        ).scalar_subquery()

        query = select(
            ((Record.end_time) - (Record.start_time)).label("time_park"),
            Record.plate,
            Record.created,
        ).where((Record.end_time - Record.start_time) == sub_query)

        filters = [Record.is_deleted == False]

        record_execute = await db.execute(query.filter(*filters))
        record = record_execute.first()
        return record

    async def get_count_capacity(
        self,
        db: Session | AsyncSession,
        zone: schemas.Zone,
        status_in: StatusRecord,
    ):
        # add id zone and id subzone
        # when have list to add set use update
        # when have int to add set use add
        zone_ids = {zone.id}
        zone_ids.update(zone.children)

        query = (
            select(func.count(Record.id))
            .where(Record.zone_id.in_(zone_ids))
            .filter(*[Record.latest_status == status_in])
        )

        return await db.scalar(query)

    async def avarage_time_referred(self, db: AsyncSession):

        query = select(
            func.avg(
                ((Record.end_time) - (Record.start_time)).label("time_park")
            )
        )
        avg_time_park = await db.scalar(query)
        avg_time_park_convert = str(timedelta(seconds=avg_time_park.seconds))

        return avg_time_park_convert

    # for worker need func sync
    def get_multi_record(
        self,
        db: Session,
        *,
        input_create_time: datetime = None,
        input_status_record: StatusRecord = None,
    ) -> list[Record]:

        query = select(Record)

        filters = [Record.is_deleted == False]

        if input_create_time is not None:
            filters.append(Record.created <= input_create_time.isoformat())

        if input_status_record is not None:
            filters.append(Record.latest_status == input_status_record)

        return self._all(db.scalars(query.filter(*filters)))


record = CRUDRecord(Record)
