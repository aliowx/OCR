from datetime import datetime, timedelta, UTC
from typing import Awaitable, Optional, List

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, and_, or_
from app import schemas
from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.record import Record
from app.schemas.record import RecordCreate, RecordUpdate, StatusRecord
from cache.redis import redis_client
from app.schemas import RecordUpdate, StatusRecord
from app.report.schemas import Timing
from app.parking.models import Zone, Equipment
from app.report.schemas import JalaliDate as JalaliDateReport
from fastapi import Query
import re


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

    def get_by_event_by_admin(
        self,
        db: Session,
        *,
        plate: schemas.Event,
        status: list[StatusRecord],
        for_update: bool = False,
    ) -> Optional[Record]:

        q = (
            db.query(Record)
            .filter(
                (Record.plate == plate.plate)
                & (Record.latest_status.in_(status))
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
                func.sum(Record.end_time - Record.start_time),
            )
            .where(and_(*filters))
            .group_by(timing)
        )
        exec = await db.execute(query)
        fetch = exec.fetchall()

        return fetch

    async def get_present_in_parking(
        self,
        db: AsyncSession,
        *,
        input_start_create_time: datetime = None,
        input_end_create_time: datetime = None,
        input_status: StatusRecord,
        zone_id: int | None = None,
    ):
        filters = [Record.is_deleted == False]

        if zone_id is not None:
            filters.append(Record.zone_id == zone_id)

        if input_start_create_time is not None:
            filters.append(Record.end_time >= input_start_create_time)

        if input_end_create_time is not None:
            filters.append(Record.start_time <= input_end_create_time)

        if input_status is not None:
            filters.append(Record.latest_status == input_status)

        query = select(Record).filter(*filters)

        records = await self._all(db.scalars(query))

        return records

    async def get_present_in_parking_count(
        self,
        db: AsyncSession,
        *,
        input_start_create_time: datetime = None,
        input_end_create_time: datetime = None,
        input_status: StatusRecord,
        zone_id: int | None = None,
    ):
        filters = [Record.is_deleted == False]

        if zone_id is not None:
            filters.append(Record.zone_id == zone_id)

        if input_start_create_time is not None:
            filters.append(Record.end_time >= input_start_create_time)

        if input_end_create_time is not None:
            filters.append(Record.start_time <= input_end_create_time)

        if input_status is not None:
            filters.append(Record.latest_status == input_status)

        query = select(func.count(Record.id)).filter(*filters)

        return await db.scalar(query)

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
        ] = Query(None),
        jalali_date: schemas.record.JalaliDate,
    ) -> list[Record] | Awaitable[list[Record]]:

        equipment_entance = aliased(Equipment)
        equipment_exit = aliased(Equipment)
        query = (
            select(
                Record,
                ((Record.end_time) - (Record.start_time)).label("time_park"),
                Zone.name,
                equipment_entance.tag.label("camera_entrance"),
                equipment_exit.tag.label("camera_exit"),
            )
            .outerjoin(Zone, Record.zone_id == Zone.id)
            .outerjoin(
                equipment_entance,
                Record.camera_entrance_id == equipment_entance.id,
            )
            .outerjoin(
                equipment_exit, Record.camera_exit_id == equipment_exit.id
            )
        )

        filters = [Record.is_deleted == False]

        # if jalali_date is not None:
        #     column_date_jalali_for_entrance = select(
        #         Record.id,
        #         func.format_jalali(Record.start_time, False).label(
        #             "date_jalali_entrance"
        #         ),
        #     ).subquery()
        #     column_date_jalali_for_exit = select(
        #         Record.id,
        #         func.format_jalali(Record.end_time, False).label(
        #             "date_jalali_exit"
        #         ),
        #     ).subquery()
        #     dj_entrance = aliased(column_date_jalali_for_entrance)
        #     dj_exit = aliased(column_date_jalali_for_exit)
        #     query = query.join(dj_entrance, Record.id == dj_entrance.c.id)
        #     query = query.join(dj_exit, Record.id == dj_exit.c.id)
        #     if jalali_date.in_start_entrance_jalali_date is not None:
        #         filters.append(
        #             dj_entrance.c.date_jalali_entrance
        #             >= jalali_date.in_start_entrance_jalali_date,
        #         )
        #     if jalali_date.in_end_entrance_jalali_date is not None:
        #         filters.append(
        #             dj_entrance.c.date_jalali_entrance
        #             <= jalali_date.in_end_entrance_jalali_date,
        #         )
        #
        #     if jalali_date.in_start_exit_jalali_date is not None:
        #         filters.append(
        #             dj_exit.c.date_jalali_exit
        #             >= jalali_date.in_start_exit_jalali_date,
        #         )
        #     if jalali_date.in_end_exit_jalali_date is not None:
        #         filters.append(
        #             dj_exit.c.date_jalali_exit
        #             <= jalali_date.in_end_exit_jalali_date,
        #         )

        if params.input_plate is not None and bool(
            re.fullmatch(r"[0-9?]{8}", params.input_plate)
        ):

            filters.append(Record.plate.like(params.input_plate))

        if params.input_camera_exit_id is not None:
            filters.append(
                Record.camera_exit_id == params.input_camera_exit_id
            )

        if params.input_camera_entrance_id is not None:
            filters.append(
                Record.camera_entrance_id == params.input_camera_entrance_id
            )

        if params.input_zone_id is not None:
            filters.append(Record.zone_id == params.input_zone_id)

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

        all_items_count = await db.scalar(
            query.filter(*filters).with_only_columns(func.count())
        )

        if params.limit is None:
            result = (
                await db.execute(
                    query.filter(*filters)
                    .offset(params.skip)
                    .order_by(
                        Record.start_time.asc()
                        if params.asc
                        else Record.start_time.desc()
                    )
                )
            ).fetchall()

            return [result, all_items_count]
        result = (
            await db.execute(
                query.filter(*filters)
                .offset(params.skip)
                .limit(params.limit)
                .order_by(
                    Record.start_time.asc()
                    if params.asc
                    else Record.start_time.desc()
                )
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

        return await self._first(
            db.scalars(query.filter(*filters).order_by(Record.id.desc()))
        )

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

    async def get_time_park(
        self,
        db: AsyncSession,
        *,
        start_time_in: datetime = None,
        end_time_in: datetime = None,
        zone_id_in: int | None = None,
        jalali_date: JalaliDateReport = None,
    ):

        query = select(
            func.sum(
                ((Record.end_time) - (Record.start_time)).label("time_park")
            ),
        )

        filters = [
            Record.is_deleted == False,
            Record.latest_status == schemas.record.StatusRecord.finished,
        ]

        # if jalali_date is not None:
        #     column_date_jalali = select(
        #         Record.id,
        #         func.format_jalali(Record.start_time, False).label(
        #             "date_jalali"
        #         ),
        #     ).subquery()
        #     dj = aliased(column_date_jalali)
        #     if (
        #         jalali_date.in_start_jalali_date is not None
        #         and jalali_date.in_end_jalali_date is not None
        #     ):
        #         query = query.join(dj, Record.id == dj.c.id).filter(
        #             *[
        #                 dj.c.date_jalali.between(
        #                     jalali_date.in_start_jalali_date,
        #                     jalali_date.in_end_jalali_date,
        #                 )
        #             ]
        #         )

        if zone_id_in is not None:
            filters.append(Record.zone_id == zone_id_in)

        if start_time_in is not None and end_time_in is not None:
            filters.append(
                Record.start_time.between(start_time_in, end_time_in)
            )

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
            filters.append(Record.start_time <= input_create_time)

        if input_status_record is not None:
            filters.append(Record.latest_status == input_status_record)

        return self._all(db.scalars(query.filter(*filters)))

    async def count_entrance_exit_door(
        self,
        db: AsyncSession,
        zone_id_in: int,
        start_time_in: datetime | None = None,
        end_time_in: datetime | None = None,
    ):
        filters = [Record.is_deleted == False]

        if start_time_in is not None and end_time_in is not None:
            filters.append(
                Record.start_time.between(start_time_in, end_time_in)
            )
        if zone_id_in is not None:
            filters.append(Record.zone_id == zone_id_in)

        camera_entrance = aliased(Equipment)
        query_entrance = (
            select(
                camera_entrance.tag,
                func.count(Record.camera_entrance_id).label("count_entrance"),
            )
            .outerjoin(
                camera_entrance,
                Record.camera_entrance_id == camera_entrance.id,
            )
            .group_by(camera_entrance.tag)
        )
        execute_query_entrance = await db.execute(
            query_entrance.filter(*filters)
        )
        fetch_query_entrance = execute_query_entrance.fetchall()

        camera_exit = aliased(Equipment)
        query_exit = (
            select(
                camera_exit.tag,
                func.count(Record.camera_exit_id).label("count_exit"),
            )
            .outerjoin(
                camera_exit,
                Record.camera_exit_id == camera_exit.id,
            )
            .group_by(camera_exit.tag)
        )

        execute_query_exit = await db.execute(query_exit.filter(*filters))
        fetch_query_exit = execute_query_exit.fetchall()

        count_entrance = {
            camera_name: count for camera_name, count in fetch_query_entrance
        }
        count_exit = {
            camera_name: count for camera_name, count in fetch_query_exit
        }

        return count_entrance, count_exit

    async def get_effective_utilization_rate(
        self,
        db: AsyncSession,
        *,
        start_time_in: datetime = None,
        end_time_in: datetime = None,
        zone_id_in: int = None,
    ):
        query = select(
            func.avg(
                ((Record.end_time) - (Record.start_time)).label("time_park")
            ),
        )

        filters = [Record.is_deleted == False, Zone.is_deleted == False]

        if zone_id_in is not None:
            filters.append(Record.zone_id == zone_id_in)

        if start_time_in is not None and end_time_in is not None:
            filters.append(
                Record.start_time.between(start_time_in, end_time_in)
            )

        result = (await db.execute(query.filter(*filters))).fetchall()

        return result


record = CRUDRecord(Record)
