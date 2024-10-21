from typing import Awaitable
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from .models import Error
from .schemas import ErrorCreate, ErrorUpdate, ParamsError


class CRUDUser(CRUDBase[Error, ErrorCreate, ErrorUpdate]):
    async def get_multi_by_filter(
        self, db: Session | AsyncSession, *, params: ParamsError
    ) -> list[Error] | Awaitable[list[Error]]:

        query = select(Error)

        filters = [Error.is_deleted == False]

        if params.input_plate is not None:
            filters.append(Error.correct_plate == params.input_plate)

        total_count = self.count_by_filter(db, filters=filters)

        order_by = Error.id.asc() if params.asc else Error.id.desc()

        if params.size is None:
            return (
                await self._all(
                    db.scalars(query.filter(*filters).order_by(order_by))
                ),
                await total_count,
            )
        return (
            await self._all(
                db.scalars(
                    query.filter(*filters)
                    .offset(params.skip)
                    .limit(params.size)
                    .order_by(order_by)
                )
            ),
            await total_count,
        )


error_repo = CRUDUser(Error)
