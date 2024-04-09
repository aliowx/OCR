import base64
from datetime import datetime
from typing import Any, Awaitable, Dict, List, Union

import rapidjson
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from app.crud.base import CRUDBase
from app import crud
from app.models.plate import Plate
from app.models.image import Image
from app.models.camera import Camera
from app.schemas.image import ImageCreateBinary
from app.schemas.plate import (
    PlateCreate,
    PlateUpdate,
    PlatesToghetherCreate,
)
from cache import redis
from app.core.config import settings

from cache.redis import redis_client


class CRUDPlate(CRUDBase[Plate, PlateCreate, PlateUpdate]):
    async def connect_redis():
        return await redis.redis_connect(settings.REDIS_URI)

    def create(*args, **wargs) -> Plate:
        db_obj = super().create(*args, **wargs)
        redis_client.publish(
            "plates:1", rapidjson.dumps(jsonable_encoder(db_obj))
        )
        return db_obj

    def create_plate(
        self, db: Session, *, obj_in: PlateCreate
    ) -> Plate:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = Plate(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        redis_client.publish(
            "plates:1", rapidjson.dumps(jsonable_encoder(db_obj))
        )
        return db_obj

    def create_with_image(
        self, db: Session, *, obj_in: PlatesToghetherCreate, owner_id: int
    ) -> Plate:
        def create_image(images):
            images = [jsonable_encoder(image) for image in images]
            for image in images:
                image["image"] = base64.b64decode(image["image"].encode())

            db_objects = [Image(**image) for image in images]
            # db_obj = Image(**image)  # type: ignore
            db.add_all(db_objects)
            db.commit()
            [db.refresh(db_obj) for db_obj in db_objects]
            return list(db_obj.id for db_obj in db_objects)

        plates = []
        obj_in = jsonable_encoder(obj_in)
        image_ids = create_image(
            [obj_in["big_image"]]
            + [plate_with_lpr["lpr"] for plate_with_lpr in obj_in["plates"]]
        )
        big_image_id = image_ids[0]  # create_image(obj_in["big_image"])

        print(big_image_id)
        for plate_with_lpr, lpr_id in zip(obj_in["plates"], image_ids[1:]):
            # lpr_id = create_image(plate_with_lpr["lpr"])
            plate_with_lpr["lpr_id"] = lpr_id
            plate_with_lpr["big_image_id"] = big_image_id
            del plate_with_lpr["lpr"]
            plate = self.create_with_owner(
                db=db,
                obj_in=plate_with_lpr,
                owner_id=owner_id,
            )
            plates.append(plate)

        return plates

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> list[Plate]:
        query = (
            select(self.model)
            .filter(Plate.owner_id == owner_id)
            .order_by(self.model.id.desc())
            .offset(skip)
        )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

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

    def get_multi_filter(
        self,
        db: Session | AsyncSession,
        *,
        record_number: int = None,
        ocr_checked: bool = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Plate] | Awaitable[list[Plate]]:
        if record_number is not None:
            query = (
                select(self.model)
                .filter(
                    Plate.record_number == record_number,
                    Plate.is_deleted == False,
                )
                .order_by(self.model.id.desc())
                .offset(skip)
            )
        elif ocr_checked is not None:
            query = (
                select(self.model)
                .filter(
                    (
                        Plate.ocr_checked.isnot(None)
                        if ocr_checked
                        else Plate.ocr_checked.is_(None)
                    ),
                    Plate.lpr_id.isnot(None),
                    Plate.is_deleted == False,
                )
                .order_by(self.model.id.desc())
                .offset(skip)
            )
        else:
            query = (
                select(self.model)
                .filter(
                    Plate.is_deleted == False,
                )
                .order_by(self.model.id.desc())
                .offset(skip)
            )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    # def update_checkoperatory(
    #     self,
    #     db: Session | AsyncSession,
    #     *,
    #     db_obj: Plate,
    #     obj_in: PlateUpdateCheckOperatory | dict[str, Any],
    # ) -> Plate | Awaitable[Plate]:
    #     obj_data = jsonable_encoder(db_obj)
    #     if isinstance(obj_in, dict):
    #         update_data = obj_in
    #     else:
    #         update_data = obj_in.dict(exclude_unset=True)
    #     for field in ["ocr_checked", "additional_data"]:
    #         # if field in update_data:
    #         setattr(db_obj, field, update_data[field])
    #     if hasattr(self.model, "modified"):
    #         setattr(db_obj, "modified", datetime.now())
    #     db.add(db_obj)
    #     return self._commit_refresh(db=db, db_obj=db_obj)

    def get_plate_pixel_info(
        self, db: Session, *, check_time: datetime, check_record_id: int
    ) -> Plate:
        return (
            db.query(self.model)
            .filter(
                Plate.record_id == check_record_id
                and Plate.record_time == check_time
            )
            .first()
        )

    def find_plates(
        self,
        db: Session | AsyncSession,
        *,
        input_ocr: str = None,
        input_camera_code: str = None,
        input_owner_id: int = None,
        input_time_min: datetime = None,
        input_time_max: datetime = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Plate] | Awaitable[list[Plate]]:

        query = select(Plate)

        if input_ocr is not None:
            query = query.filter(
                Plate.ocr == input_ocr, Plate.is_deleted == False
            )

        if input_camera_code:
            # join Plate with User
            query = query.join(Camera)
            query = query.filter(
                Camera.camera_code == input_camera_code,
                Camera.is_deleted == False,
            )

        if input_owner_id:
            query = query.filter(
                Plate.owner_id == input_owner_id, Plate.is_deleted == False
            )

        if input_time_min is not None:
            query = query.filter(
                Plate.record_time >= input_time_min, Plate.is_deleted == False
            )

        if input_time_max is not None:
            query = query.filter(
                Plate.record_time <= input_time_max, Plate.is_deleted == False
            )

        if limit is None:
            return self._all(db.scalars(query.offset(skip)))
        return self._all(db.scalars(query.offset(skip).limit(limit)))

    def get_random_plate_by_camera_id(
        self, db: Session | AsyncSession, *, camera_id: int
    ) -> Any:

        return self._first(
            db.scalars(
                select(Plate)
                .order_by(func.random())
                .filter(Plate.camera_id == camera_id)
                .filter(Plate.big_image_id != None)
                .limit(100)
            )
        )


plate = CRUDPlate(Plate)
