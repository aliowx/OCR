from typing import Awaitable
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from .models.plate import PlateList
from .schemas import PlateCreate, PlateUpdate, ParamsPlate, PlateType
import re


class CRUDPlate(CRUDBase[PlateList, PlateCreate, PlateUpdate]):
    async def get_multi_by_filter(
        self, db: Session | AsyncSession, *, params: ParamsPlate
    ) -> list[PlateList] | Awaitable[list[PlateList]]:

        query = select(PlateList)

        filters = [PlateList.is_deleted == False]

        if params.input_plate is not None and bool(
            re.fullmatch(r"[0-9?]{9}", params.input_plate)
        ):
            value_plate = params.input_plate.replace("?", "_")
            filters.append(PlateList.plate.like(value_plate))

        if params.input_name is not None:
            if "%" not in params.input_name:
                filters.append(PlateList.name.ilike(f"%{params.input_name}%"))

        if params.input_type is not None:
            filters.append(PlateList.type == params.input_type)

        total_count = await self.count_by_filter(db, filters=filters)

        order_by = PlateList.id.asc() if params.asc else PlateList.id.desc()

        if params.size is None:
            resualt = await self._all(
                db.scalars(query.filter(*filters).order_by(order_by))
            )
            return resualt, total_count
        resualt = await self._all(
            db.scalars(
                query.filter(*filters)
                .offset(params.skip)
                .limit(params.size)
                .order_by(order_by)
            )
        )
        return resualt, total_count

    async def get_multi_by_plate(
        self,
        db: AsyncSession,
        *,
        plate: list[str],
        type_list: PlateType | None = None,
    ) -> PlateList:

        query = select(PlateList.plate)

        filters = [PlateList.is_deleted == False]

        if plate is not None:
            filters.append(PlateList.plate.in_(plate))

        if type_list is not None:
            filters.append(PlateList.type == type_list)

        return await self._all(db.scalars(query.filter(*filters)))

    async def get_plate(
        self,
        db: AsyncSession,
        *,
        plate: str,
        type_list: PlateType | None = None,
        phone_number: str | None = None,
    ) -> PlateList:

        query = select(PlateList)

        filters = [
            PlateList.is_deleted == False,
            and_(
                PlateList.plate == plate,
                PlateList.type == type_list,
                PlateList.phone_number == phone_number,
            ),
        ]
        return await self._first(db.scalars(query.filter(*filters)))
    
    async def exist_plate(
        self,
        db: AsyncSession,
        *,
        plate: str,
        type_list: PlateType | None = None,
    ) -> PlateList:

        query = select(PlateList)

        filters = [
            PlateList.is_deleted == False,
            and_(
                PlateList.plate == plate,
                PlateList.type == type_list
            ),
        ]
        return await self._first(db.scalars(query.filter(*filters)))

    async def cheking_and_create_phone_number(
        self,
        db: AsyncSession,
        *,
        plate: str,
        phone_number: str,
        type_list: PlateType | None = None,
    ) -> PlateList:

        exist_plates_phone = await self.get_plate(
            db,
            plate=plate,
            type_list=type_list,
            phone_number=phone_number,
        )
        if not exist_plates_phone:
            exist_plates_phone = await self.create(
                db,
                obj_in=PlateCreate(
                    type=type_list,
                    plate=plate,
                    phone_number=phone_number,
                ),
            )
        return exist_plates_phone

    async def cheking_palte_have_phone_number(
        self,
        db: AsyncSession,
        *,
        plate: str,
        type_list: PlateType | None = None,
    ) -> PlateList:

        exist_plates_phone = await self.exist_plate(
            db,
            plate=plate,
            type_list=type_list,
        )

        return exist_plates_phone


plate_repo = CRUDPlate(PlateList)
