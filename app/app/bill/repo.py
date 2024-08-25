from .models import Bill
from app.crud.base import CRUDBase
from .schemas.bill import (
    BillCreate,
    BillUpdate,
    ParamsBill,
    Bill as billschemas,
    PaymentBillCreate,
    PaymentBillUpdate,
)
from app.bill.models import PaymentBill
from sqlalchemy import false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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

        if params.input_start_time is not None:
            filters.append(Bill.created >= params.input_start_time)

        if params.input_end_time is not None:
            filters.append(Bill.created <= params.input_end_time)

        if params.input_issued_by is not None:
            filters.append(Bill.issued_by == params.input_issued_by)

        count = await self.count_by_filter(db, filters=filters)

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


class PaymentBillRepository(
    CRUDBase[PaymentBill, PaymentBillCreate, PaymentBillUpdate]
): ...


payment_bill_repo = PaymentBillRepository(PaymentBill)
bill_repo = BillRepository(Bill)
