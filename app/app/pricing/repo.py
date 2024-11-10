import logging
from typing import Awaitable

from sqlalchemy import and_, false, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.parking.models import Zone
from app.crud.base import CRUDBase

from .models import Price
from .schemas import PriceCreate, PriceUpdate, ReadPricesParams

logger = logging.getLogger(__name__)


class PriceRepository(CRUDBase[Price, PriceCreate, PriceUpdate]):

    async def get_by_name(
        self, db: AsyncSession, name: str, except_id: int = None
    ) -> Price | None:

        filters = [
            func.lower(self.model.name) == name.lower(),
            self.model.is_deleted == false(),
        ]
        # find name except self for update
        if except_id is not None:
            filters.append(self.model.id != except_id)

        price = await self._first(
            db.scalars(select(self.model).filter(*filters))
        )
        return price

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        params: ReadPricesParams,
    ) -> tuple[list[Price], int]:

        query = select(Price)

        filters = [self.model.is_deleted == false()]

        if params.name is not None:
            filters.append(Price.name == params.name)

        count = self.count_by_filter(db, filters=filters)

        order_by = self.model.id.asc() if params.asc else self.model.id.desc()
        query = query.order_by(order_by)

        if params.size is None:
            return (
                await self._all(
                    db.scalars(
                        query.filter(*filters)
                        .offset(params.skip)
                        .order_by(order_by)
                    )
                ),
                await count,
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
            await count,
        )


price_repo = PriceRepository(Price)
