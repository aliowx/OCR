from .models import Bill
from app.crud.base import CRUDBase
from .schemas.bill import (
    BillCreate,
    BillUpdate,
    ParamsBill,
    Bill as billschemas,
)
from sqlalchemy import false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, UTC
from app.models import Record


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

        query = select(Bill).join(Record, Bill.record_id == Record.id)

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

        count = await self.count_by_filter(db, filters=filters)

        order_by = Bill.id.asc() if params.asc else Bill.id.desc()

        # exec = await db.execute(query.filter(*filters))

        # fetch = exec.fetchall()
        # print(fetch)
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

    async def get_all_by_ids(self, db: AsyncSession, *, ids: int):

        return await self._all(
            db.scalars(
                select(Bill).filter(
                    *[Bill.is_deleted == false(), Bill.id.in_(ids)]
                )
            )
        )

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


bill_repo = BillRepository(Bill)
