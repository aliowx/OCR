from datetime import datetime, timedelta, UTC
from typing import Awaitable, Optional, List

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, and_
from app import schemas
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.record import Record
from app.schemas.record import RecordCreate, RecordUpdate
from cache.redis import redis_client
from app.schemas import RecordUpdate, StatusRecord
from app.report.schemas import Timing
from app.parking.models import Zone, Equipment
from app.models.image import Image
from fastapi import Query


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
        for_update: bool = False,
    ) -> Optional[Record]:

        offset = timedelta(
            seconds=settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR
        )
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
            Record.start_time.between(
                input_start_create_time, input_end_create_time
            )
        )

        return await db.scalar(
            query.with_only_columns(func.count()).filter(*filters)
        )

    async def get_count_referred_by_timing_status(
        self,
        db: AsyncSession,
        *,
        input_start_create_time: datetime = None,
        input_end_create_time: datetime = None,
        timing: Timing,
        zone_id: int | None = None,
    ):
        filters = [
            Record.is_deleted == False,
            Record.start_time.between(
                input_start_create_time, input_end_create_time
            ),
        ]

        if zone_id is not None:
            filters.append(Record.zone_id == zone_id)

        query = (
            select(
                (func.date_trunc(timing, Record.start_time)).label(timing),
                func.count(Record.id).label("count"),
                Record.latest_status,
            )
            .where(and_(*filters))
            .group_by(timing)
            .group_by(Record.latest_status)
            .order_by(timing)
        )
        exec = await db.execute(query)
        fetch = exec.fetchall()

        return fetch

    async def get_count_referred_with_out_status(
        self,
        db: AsyncSession,
        *,
        input_start_create_time: datetime = None,
        input_end_create_time: datetime = None,
        timing: Timing,
        zone_id: int | None = None,
    ):
        filters = [
            Record.is_deleted == False,
            Record.start_time.between(
                input_start_create_time, input_end_create_time
            ),
        ]

        if zone_id is not None:
            filters.append(Record.zone_id == zone_id)

        query = (
            select(
                func.date_trunc(timing, Record.start_time).label(timing),
                func.count(Record.id).label("count"),
            )
            .where(and_(*filters))
            .group_by(timing)
            .order_by(timing)
        )
        exec = await db.execute(query)
        fetch = exec.fetchall()

        return fetch

    async def get_today_count_referred_by_zone(
        self,
        db: Session | AsyncSession,
        *,
        zone_id: int = None,
        start_time_in: datetime,
        end_time_in: datetime,
    ):

        query = select(Record)

        filters = [
            Record.is_deleted == False,
            Record.start_time.between(start_time_in, end_time_in),
            Record.zone_id == zone_id,
        ]

        return await db.scalar(
            query.with_only_columns(func.count()).filter(*filters)
        )

    async def get_multi_by_filters(
        self,
        db: Session | AsyncSession,
        *,
        params: schemas.ParamsRecord,
        input_status_record: Optional[
            List[schemas.record.StatusRecord]
        ] = Query(
            None
        ),  # List of StatusRecord as query parameter
    ) -> list[Record] | Awaitable[list[Record]]:

        img_entrance = aliased(Image)
        equipment_entance = aliased(Equipment)
        img_exit = aliased(Image)
        equipment_exit = aliased(Equipment)
        query = (
            select(
                Record,
                ((Record.end_time) - (Record.start_time)).label("time_park"),
                Zone.name,
                equipment_entance.serial_number.label("camera_entrance"),
                equipment_exit.serial_number.label("camera_exit"),
            )
            .join(Zone, Record.zone_id == Zone.id)
            .join(img_entrance, Record.img_entrance_id == img_entrance.id)
            .join(
                equipment_entance,
                img_entrance.camera_id == equipment_entance.id,
            )
            .join(img_exit, Record.img_exit_id == img_exit.id)
            .join(equipment_exit, img_exit.camera_id == equipment_exit.id)
        )

        filters = [Record.is_deleted == False]

        if params.input_plate is not None:
            filters.append(Record.plate.ilike(params.input_plate))

        if params.input_zone_id is not None:
            filters.append(Record.zone_id == params.input_zone_id)

        if params.input_created_start_time is not None:
            filters.append(Record.created >= params.input_created_start_time)

        if params.input_created_end_time is not None:
            filters.append(Record.created <= params.input_created_end_time)

        if params.input_entrance_start_time is not None:
            filters.append(
                Record.start_time >= params.input_entrance_start_time
            )

        if params.input_entrance_end_time is not None:
            filters.append(Record.start_time <= params.input_entrance_end_time)

        if params.input_exit_start_time is not None:
            filters.append(Record.end_time >= params.input_exit_start_time)

        if params.input_exit_end_time is not None:
            filters.append(Record.end_time <= params.input_exit_end_time)

        if input_status_record is not None:
            filters.append(Record.latest_status.in_(input_status_record))

        if params.input_score is not None:
            filters.append(Record.score >= params.input_score)

        all_items_count = await self.count_by_filter(db, filters=filters)

        if params.limit is None:
            result = (
                await db.execute(query.filter(*filters).offset(params.skip))
            ).fetchall()

            return [result, all_items_count]
        result = (
            await db.execute(
                query.filter(*filters)
                .offset(params.skip)
                .limit(params.limit)
                .order_by(Record.id.asc() if params.asc else Record.id.desc())
            )
        ).fetchall()

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

    async def get_count_unknown_referred(
        self,
        db: AsyncSession,
    ):
        return await db.scalar(
            select(func.count(Record.id)).filter(
                *[
                    Record.is_deleted == False,
                    Record.latest_status == StatusRecord.unknown.value,
                ]
            )
        )

    async def get_count_capacity(
        self,
        db: Session | AsyncSession,
        zone: schemas.Zone,
        status_in: list[StatusRecord],
    ):

        zone_ids = {zone.id}
        zone_ids.update(zone.children)
        query = (
            select(func.count(Record.id))
            .where(Record.zone_id.in_(zone_ids))
            .filter(*[Record.latest_status.in_(status_in)])
        )

        return await db.scalar(query)

    async def get_avg_time_park(
        self,
        db: AsyncSession,
        *,
        start_time_in: datetime = None,
        end_time_in: datetime = None,
        zone_id_in: int | None = None,
    ):

        query = select(
            func.avg(
                ((Record.end_time) - (Record.start_time)).label("time_park")
            ),
        )

        filters = [Record.is_deleted == False]

        if zone_id_in is not None:
            filters.append(Record.zone_id == zone_id_in)

        if start_time_in is not None:
            filters.append(Record.start_time >= start_time_in)

        if end_time_in is not None:
            filters.append(Record.start_time <= end_time_in)

        avg_time_park = await db.scalar(query.filter(*filters))

        return avg_time_park

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
            filters.append(Record.start_time >= input_create_time)

        if input_status_record is not None:
            filters.append(Record.latest_status == input_status_record)

        return self._all(db.scalars(query.filter(*filters)))


record = CRUDRecord(Record)
