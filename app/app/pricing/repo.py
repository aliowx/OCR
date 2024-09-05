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

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: ReadPricesParams,
        asc: bool = False,
    ) -> tuple[list[Price], int]:

        query = select(Price, Zone).where(self.model.is_deleted == false())

        if filters.zone_id is not None:
            query = query.where(Zone.id == filters.zone_id)
        if filters.name:
            query = query.where(Price.name == filters.name)

        count = query.with_only_columns(func.count())
        total_count = await db.scalar(count)
        order_by = self.model.id.asc() if asc else self.model.id.desc()
        query = query.order_by(order_by)

        if filters.size is None:
            query = query.offset(filters.skip)

        if filters.skip:
            query = query.offset(filters.skip).limit(filters.size)

        execute_query = await db.execute(query)
        query_fetch = execute_query.fetchall()
        return query_fetch, total_count


price_repo = PriceRepository(Price)
