from typing import Awaitable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from .models.plate import PlateList
from .schemas import PlateCreate, PlateUpdate, ParamsPlate
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
            filters.append(PlateList.name == params.input_name)

        if params.input_expire_start is not None:
            filters.append(PlateList.expire_start >= params.input_expire_start)

        if params.input_expire_end is not None:
            filters.append(PlateList.expire_end <= params.input_expire_end)

        if params.input_status is not None:
            filters.append(PlateList.status == params.input_status)

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

    async def get_by_plate(
        self, db: AsyncSession, *, plate: list[str]
    ) -> PlateList:

        query = select(PlateList.plate)

        filters = [PlateList.is_deleted == False]

        if plate is not None:
            filters.append(PlateList.plate.in_(plate))

        return await self._all(db.scalars(query.filter(*filters)))


plate_repo = CRUDPlate(PlateList)
