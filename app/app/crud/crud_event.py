from datetime import datetime, UTC
from typing import Awaitable

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.event import Event
from app.parking.models.equipment import Equipment
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    ParamsEvents,
    ReportDoor,
)
from cache.redis import redis_client
import re


class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    def create(
        self,
        db: Session | AsyncSession,
        *,
        obj_in: EventCreate | dict,
        commit: bool = True,
    ) -> Event | Awaitable[Event]:
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
            "events:1", rapidjson.dumps(jsonable_encoder(db_obj))
        )
        return self._commit_refresh(db=db, db_obj=db_obj, commit=commit)

    async def find_events(
        self, db: Session | AsyncSession, *, params: ParamsEvents
    ) -> list[Event] | Awaitable[list[Event]]:

        query = select(Event)

        filters = [Event.is_deleted == False]

        if params.input_plate is not None and bool(
            re.fullmatch(r"[0-9?]{9}", params.input_plate)
        ):
            value_plate = params.input_plate.replace("?", "_")
            filters.append(Event.plate.like(value_plate))

        if params.similar_plate is not None:
            # Adjust similarity threshold if necessary
            await db.execute(text("SET pg_trgm.similarity_threshold = 0.5"))
            filters.append(text(f"plate % :similar_plate"))

        if params.input_camera_id is not None:
            filters.append(Event.camera_id == params.input_camera_id)

        if params.input_time_min is not None:
            filters.append(Event.record_time >= params.input_time_min)

        if params.input_record_id is not None:
            filters.append(Event.record_id == params.input_record_id)

        if params.input_time_max is not None:
            filters.append(Event.record_time <= params.input_time_max)

        if params.size is None:
            return await self._all(
                db.scalars(
                    query.filter(*filters).offset(params.skip),
                    (
                        {}
                        if params.similar_plate is None
                        else {"similar_plate": params.similar_plate}
                    ),
                )
            )

        all_items_count = await self.count_by_filter(
            db,
            filters=filters,
            params=(
                {}
                if params.similar_plate is None
                else {"similar_plate": params.similar_plate}
            ),
        )

        items = await self._all(
            db.scalars(
                query.filter(*filters).offset(params.skip).limit(params.size),
                (
                    {}
                    if params.similar_plate is None
                    else {"similar_plate": params.similar_plate}
                ),
            )
        )

        return [items, all_items_count]

    async def get_events_by_record_ids(
        self, db: AsyncSession, *, record_ids: list[int]
    ) -> list[Event] | Awaitable[list[Event]]:
        return await self._all(
            db.scalars(
                select(Event)
                .filter(
                    *[
                        Event.record_id.in_(record_ids),
                        Event.is_deleted == False,
                    ]
                )
                .with_for_update()
            )
        )

    async def remove_by_record_id(
        db: AsyncSession,
        record_id: int,
    )-> bool:
        
        query = select(Event).filter(Event.record_id == record_id)
        result = await db.execute(query)
        events = result.scalars().all()

        if events:
            for event in events:
                db.delete(event)
            await db.commit()
            return True
        return False        
    
    
    
event = CRUDEvent(Event)
