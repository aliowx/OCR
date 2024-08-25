from .models import Payment
from app.crud.base import CRUDBase
from .schemas.payment import PaymentCreate, PaymentUpdate, ParamsPayment

from sqlalchemy import false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class PaymentRepository(CRUDBase[Payment, PaymentCreate, PaymentUpdate]):

    async def get_multi_by_filters(
        self, db: AsyncSession, *, params: ParamsPayment
    ) -> tuple[list[Payment], int]:

        query = select(Payment)

        filters = [Payment.is_deleted == false()]

        if params.input_status is not None:
            filters.append(Payment.status == params.input_status)
        if params.input_price is not None:
            filters.append(Payment.price == params.input_price)

        if params.input_tracking_code is not None:
            filters.append(Payment.tracking_code == params.input_tracking_code)

        count = await self.count_by_filter(db, filters=filters)

        order_by = Payment.id.asc() if params.asc else Payment.id.desc()

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


payment_repo = PaymentRepository(Payment)
