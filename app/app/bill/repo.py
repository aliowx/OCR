from .models import Bill
from app.crud.base import CRUDBase
from .schemas.bill import (
    BillCreate,
    BillUpdate,
    ParamsBill,
    Bill as billschemas,
    StatusBill,
)
from app.report.schemas import Timing
from sqlalchemy import false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from datetime import datetime, UTC
from typing import Awaitable
from app.models import Record, Image
from app.parking.models import Equipment


class BillRepository(CRUDBase[Bill, BillCreate, BillUpdate]):

    async def get_bill_by_plate(
        self, db: AsyncSession, plate_in: str = None
    ) -> Bill:

        query = select(Bill)

        filters = [Bill.is_deleted == false()]

        if plate_in is not None:
            filters.append(Bill.plate == plate_in)

        return await self._first(
            db.scalars(query.order_by(Bill.created.desc()).filter(*filters))
        )

    async def get_multi_by_filters(
        self, db: AsyncSession, *, params: ParamsBill
    ) -> tuple[list[billschemas], int]:

        query = select(Bill)

        filters = [Bill.is_deleted == false()]

        if params.input_plate is not None:
            filters.append(Bill.plate == params.input_plate)

        if params.input_zone_id is not None:
            filters.append(Record.zone_id == params.input_zone_id)

        if params.input_start_time is not None:
            filters.append(Bill.created >= params.input_start_time)

        if params.input_end_time is not None:
            filters.append(Bill.created <= params.input_end_time)

        if params.input_issued_by is not None:
            filters.append(Bill.issued_by == params.input_issued_by)

        if params.input_status is not None:
            filters.append(Bill.status == params.input_status)

        count = await db.scalar(
            query.with_only_columns(func.count()).filter(*filters)
        )

        order_by = Bill.id.asc() if params.asc else Bill.id.desc()

        if params.size is None:
            items = await self._all(
                db.scalars(
                    query.order_by(order_by)
                    .offset(params.skip)
                    .filter(*filters)
                )
            )

            return (items, count)

        items = await self._all(
            db.scalars(
                query.order_by(order_by)
                .limit(params.size)
                .offset(params.skip)
                .filter(*filters)
            )
        )
        return (items, count)

    async def get_multi_bills(self, db: AsyncSession, *, record_ids: int):

        return await self._all(
            db.scalars(
                select(Bill).filter(
                    *[
                        Bill.is_deleted == false(),
                        Bill.record_id.in_(record_ids),
                    ]
                )
            )
        )

    async def get_total_amount_bill(self, db: AsyncSession):

        return await db.scalar(
            select(func.sum(Bill.price)).filter(
                Bill.is_deleted == False,
                Bill.created
                >= datetime.now(UTC).replace(
                    tzinfo=None, hour=0, minute=0, second=0, microsecond=0
                ),
            )
        )

    async def get_camera_by_image_id(self, db: AsyncSession, img_id: int):

        query = (
            select(Equipment.serial_number)
            .select_from(Bill)
            .join(Image, img_id == Image.id)
            .join(Equipment, Image.camera_id == Equipment.id)
        )

        return await db.scalar(query.filter(*[Bill.is_deleted == False]))

    async def get_total_price_count(
        self,
        db: AsyncSession,
        *,
        zone_id: int,
        start_time_in: datetime,
        end_time_in: datetime
    ):

        filters = [Bill.is_deleted == False]

        if zone_id is not None:
            filters.append(Bill.zone_id == zone_id)
        if start_time_in is not None:
            filters.append(Bill.created >= start_time_in)
        if end_time_in is not None:
            filters.append(Bill.created <= end_time_in)

        query_total_count_price = select(
            func.sum(Bill.price),
            func.count(Bill.id),
        ).filter(*filters)

        excute_query_total_count_price = await db.execute(
            query_total_count_price
        )
        fetch_query_total_count_price = (
            excute_query_total_count_price.fetchone()
        )

        query_get_paid_price_count = select(
            func.sum(Bill.price), func.count()
        ).filter(*filters, Bill.status == StatusBill.paid)

        excute_query_get_paid_price_count = await db.execute(
            query_get_paid_price_count
        )
        fetch_query_get_paid_price_count = (
            excute_query_get_paid_price_count.fetchone()
        )

        query_get_unpaid_price_count = select(
            func.sum(Bill.price), func.count()
        ).filter(*filters, Bill.status == StatusBill.unpaid)

        excute_query_get_unpaid_price_count = await db.execute(
            query_get_unpaid_price_count
        )
        fetch_query_get_unpaid_price_count = (
            excute_query_get_unpaid_price_count.fetchone()
        )

        return (
            fetch_query_total_count_price,
            fetch_query_get_paid_price_count,
            fetch_query_get_unpaid_price_count,
        )

    async def get_total_price_by_timing(
        self,
        db: AsyncSession,
        *,
        timing: Timing,
        zone_id: int,
        start_time_in: datetime,
        end_time_in: datetime
    ):

        filters = [Bill.is_deleted == False]

        if zone_id is not None:
            filters.append(Bill.zone_id == zone_id)
        if start_time_in is not None:
            filters.append(Bill.created >= start_time_in)
        if end_time_in is not None:
            filters.append(Bill.created <= end_time_in)

        query = select(
            func.date_trunc(timing, Bill.created).label(timing),
            func.sum(Bill.price),
        ).filter(*filters).group_by(timing)

        excute_query_total_count_price = await db.execute(query)
        fetch_query_total_price = excute_query_total_count_price.fetchall()

        return fetch_query_total_price

    async def get(
        self, db: AsyncSession, id: int, for_update: bool = False
    ) -> Bill | Awaitable[Bill]:

        query = select(self.model).filter(
            self.model.id == id, self.model.is_deleted == False
        )
        if for_update:
            return await self._first(db.scalars(query.with_for_update()))

        return await self._first(db.scalars(query))

    async def avg_price_per_referred(self, db: AsyncSession):

        query = select(
            func.count(Bill.record_id).label("count"),
            func.sum(Bill.price).label("price"),
        ).where(and_(Bill.record_id != None, Bill.is_deleted == False))

        execute = await db.execute(query)

        count, total_price = execute.fetchone()

        if count is None or count == 0:
            return 0

        return total_price / count


bill_repo = BillRepository(Bill)
