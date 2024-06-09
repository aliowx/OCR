import logging

from sqlalchemy import and_, false, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.parking.models.parking import ParkingZonePrice

from .models import Price
from .schemas import PriceCreate, PriceUpdate, ReadPricesFilter

logger = logging.getLogger(__name__)


class PriceRepository(CRUDBase[Price, PriceCreate, PriceUpdate]):
    def _build_filters(self, filters: ReadPricesFilter) -> list:
        orm_filters = []
        if filters.name__contains:
            orm_filters.append(
                self.model.name.contains(filters.name__contains)
            )
        if filters.name_fa__contains:
            orm_filters.append(
                self.model.name_fa.contains(filters.name_fa__contains)
            )
        if filters.parking_id__eq:
            orm_filters.append(self.model.parking_id == filters.parking_id__eq)
        if filters.zone_id__eq:
            orm_filters.append(
                and_(
                    ParkingZonePrice.zone_id == filters.zone_id__eq,
                    ParkingZonePrice.is_deleted == false(),
                    ParkingZonePrice.price_id == self.model.id,
                )
            )
        if filters.expiration_datetime__gte:
            orm_filters.append(
                self.model.expiration_datetime
                >= filters.expiration_datetime__gte
            )
        if filters.expiration_datetime__lte:
            orm_filters.append(
                self.model.expiration_datetime
                <= filters.expiration_datetime__lte
            )
        if filters.created__gte:
            orm_filters.append(self.model.created >= filters.created__gte)
        if filters.created__lte:
            orm_filters.append(self.model.created <= filters.created__lte)
        return orm_filters

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: ReadPricesFilter,
        asc: bool = False,
    ) -> tuple[list[Price], int]:
        query = select(Price)

        if filters.join_pricezone:
            query.join(
                ParkingZonePrice, self.model.id == ParkingZonePrice.price_id
            )

        orm_filters = self._build_filters(filters)

        query = query.filter(
            self.model.is_deleted == false(),
            *orm_filters,
        )

        q = query.with_only_columns(func.count())
        total_count = db.scalar(q)

        order_by = self.model.id.asc() if asc else self.model.id.desc()
        query = query.order_by(order_by)

        if filters.limit is None:
            return (
                await self._all(db.scalars(query.offset(filters.skip))),
                await total_count,
            )
        return (
            await self._all(
                db.scalars(query.offset(filters.skip).limit(filters.limit))
            ),
            await total_count,
        )


price_repo = PriceRepository(Price)
