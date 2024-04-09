from datetime import datetime, timedelta
from typing import Any, Awaitable, Dict, List, Optional, Union

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import schemas
from app.core.config import settings
from app.crud.base import CRUDBase
from app.crud import plate
from app.models.record import Record
from app.models.plate import Plate
from app.models.user import User
from app.schemas.record import (
    RecordCreate,
    RecordUpdate,
    RecordUpdateCheckOperatory,
)
from cache.redis import redis_client


class CRUDRecord(CRUDBase[Record, RecordCreate, RecordUpdate]):
    def create(*args, **wargs) -> Record:
        db_obj = super().create(*args, **wargs)
        redis_client.publish(
            "records:1", rapidjson.dumps(jsonable_encoder(db_obj))
        )
        return db_obj

    def create_with_owner(
        self,
        db: AsyncSession | Session,
        *,
        obj_in: RecordCreate,
        owner_id: int,
    ) -> Record:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        redis_client.publish(
            "records:1", rapidjson.dumps(jsonable_encoder(db_obj))
        )
        return self._commit_refresh(db=db, db_obj=db_obj)

    def get_multi_by_owner(
        self,
        db: Session | AsyncSession,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int | None = 100,
    ) -> list[Record] | Awaitable[Record]:
        query = (
            select(self.model)
            .filter(Record.owner_id == owner_id)
            .order_by(self.model.id.desc())
            .offset(skip)
        )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    def get_multi_filter(
        self,
        db: Session | AsyncSession,
        *,
        record_number: int = None,
        ocr_checked: bool = None,
        score: float = 0,
        skip: int = 0,
        limit: int = 100,
        asc: bool = False,
    ) -> list[Record] | Awaitable[list[Record]]:
        if record_number is not None:
            query = (
                select(Record)
                .filter(
                    Record.record_number == record_number,
                    Record.score >= score,
                )
                .order_by(Record.id.asc() if asc else Record.id.desc())
                .offset(skip)
            )
        elif ocr_checked is not None:
            query = (
                select(self.model)
                .filter(
                    (
                        Record.ocr_checked.isnot(None)
                        if ocr_checked
                        else Record.ocr_checked.is_(None)
                    ),
                    Record.best_lpr_id.isnot(None),
                    Record.score >= score,
                )
                .order_by(Record.id.asc() if asc else Record.id.desc())
                .offset(skip)
            )
        else:
            query = (
                select(Record)
                .filter(Record.score >= score)
                .order_by(Record.id.asc() if asc else Record.id.desc())
                .offset(skip)
            )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    def update_checkoperatory(
        self,
        db: Session | AsyncSession,
        *,
        db_obj: Record,
        obj_in: RecordUpdateCheckOperatory | dict[str, Any],
    ) -> Record | Awaitable[Record]:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in ["ocr_checked", "additional_data"]:
            # if field in update_data:
            setattr(db_obj, field, update_data[field])
        return self.update(db=db, db_obj=db_obj)

    def get_by_plate_id(
        self,
        db: Session,
        *,
        plate_id: int,
        for_update: bool = False,
    ) -> Optional[Record]:
        plate_ = plate.get(db, id=plate_id)
        q = db.query(Record).filter(self.model.id == plate_.record_id)
        # if plate_ is None:
        #     return None
        # record_id = plate_.record_id
        # if record_id is None:
        #     return None
        # return self.get(db, id=record_id)

        if for_update:
            return q.with_for_update().first()
        else:
            return q.first()
        # return plate_.record

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

    def find_records(
        self,
        db: Session | AsyncSession,
        *,
        input_ocr: str = None,
        input_start_time_min: datetime = None,
        input_start_time_max: datetime = None,
        input_end_time_min: datetime = None,
        input_end_time_max: datetime = None,
        input_score: float = None,
        input_gateway_name: int = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Record] | Awaitable[list[Record]]:

        query = select(Record)

        if input_ocr is not None:
            query = query.filter(
                Record.ocr == input_ocr, Record.is_deleted == False
            )

        if input_start_time_min is not None:
            query = query.filter(
                Record.start_time >= input_start_time_min,
                Record.is_deleted == False,
            )

        if input_start_time_max is not None:
            query = query.filter(
                Record.start_time <= input_start_time_max,
                Record.is_deleted == False,
            )

        if input_end_time_min is not None:
            query = query.filter(
                Record.end_time >= input_end_time_min,
                Record.is_deleted == False,
            )

        if input_end_time_max is not None:
            query = query.filter(
                Record.end_time <= input_end_time_max,
                Record.is_deleted == False,
            )

        if input_score is not None:
            query = query.filter(
                Record.score == input_score, Record.is_deleted == False
            )

        if input_gateway_name is not None:
            query = query.filter(
                Record.owner_id == input_gateway_name,
                Record.is_deleted == False,
            )

        query = query.offset(skip)

        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))


record = CRUDRecord(Record)
