import logging
from typing import Awaitable

from sqlalchemy import and_, false, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.parking.models.parking import ParkingZonePrice

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
            query.join(
                ParkingZonePrice, self.model.id == ParkingZonePrice.price_id
            )

        orm_filters = [self.model.is_deleted == false()]

        if filters.name:
            orm_filters.append(self.model.name.contains(filters.name))
        if filters.name_fa:
            orm_filters.append(self.model.name_fa.contains(filters.name_fa))
        if filters.parking_id:
            orm_filters.append(self.model.parking_id == filters.parking_id)
        if filters.zone_id:
            orm_filters.append(
                and_(
                    ParkingZonePrice.zone_id == filters.zone_id,
                    ParkingZonePrice.is_deleted == false(),
                    ParkingZonePrice.price_id == self.model.id,
                )
            )
        if filters.expiration_datetime_start:  # gte
            orm_filters.append(
                self.model.expiration_datetime
                >= filters.expiration_datetime_start
            )
        if filters.expiration_datetime_end:  # lte
            orm_filters.append(
                self.model.expiration_datetime
                <= filters.expiration_datetime_end
            )
        if filters.start_date:
            orm_filters.append(self.model.created >= filters.start_date)
        if filters.end_date:
            orm_filters.append(self.model.created <= filters.end_date)

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

    async def find_model_price(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        input_name_fa_price: str = None,
    ) -> list[Price] | Awaitable[list[Price]]:

        query = select(Price)

        filters = [Price.is_deleted == false()]

        if input_name_fa_price is not None:
            filters.append(Price.name_fa.like(f"%{input_name_fa_price}%"))

        return await self._all(
            db.scalars(query.filter(*filters).offset(skip).limit(limit))
        )


price_repo = PriceRepository(Price)
