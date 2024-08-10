import logging
from typing import Awaitable

from sqlalchemy import and_, false, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.parking.models.parking import ZonePrice

from .models import Price
from .schemas import PriceCreate, PriceUpdate, ReadPricesParams

logger = logging.getLogger(__name__)


class PriceRepository(CRUDBase[Price, PriceCreate, PriceUpdate]):

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: ReadPricesParams,
        asc: bool = False,
    ) -> tuple[list[Price], int]:

        query = select(Price)

        if filters.zone_id is not None:
            query.join(ZonePrice, self.model.id == ZonePrice.price_id)

        orm_filters = [self.model.is_deleted == false()]

        if filters.name:
            orm_filters.append(Price.name == filters.name)
        if filters.name_fa:
            orm_filters.append(Price.name_fa == filters.name_fa)
        if filters.zone_id:
            orm_filters.append(
                and_(
                    ZonePrice.zone_id == filters.zone_id,
                    ZonePrice.is_deleted == false(),
                    ZonePrice.price_id == self.model.id,
                )
            )
        query = query.filter(*orm_filters)

        q = query.with_only_columns(func.count())
        total_count = db.scalar(q)

        order_by = self.model.id.asc() if asc else self.model.id.desc()
        query = query.order_by(order_by)

        if filters.size is None:
            return (
                await self._all(db.scalars(query.offset(filters.skip))),
                await total_count,
            )
        return (
            await self._all(
                db.scalars(query.offset(filters.skip).limit(filters.size))
            ),
            await total_count,
        )


price_repo = PriceRepository(Price)
