import logging
from app.core.config import settings
from app.bill.models import Bill
from app.crud.base import CRUDBase
from app.bill.schemas.bill import (
    BillCreate,
    BillUpdate,
    StatusBill,
)
from app.payment.schemas.payment import (
    BillPaymentSchemaPOS,
    SumBillsByIdSchema,
    BillPaymentSchemaIPG,
    TransactionUpdate,
    TransactionCreate,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_

from sqlalchemy.sql.expression import false, null
from app.core import exceptions as exc
from app.utils import MessageCodes, make_requests
from httpx import BasicAuth
from app import models
import httpx
from typing import Awaitable

logger = logging.getLogger(__name__)


class PaymentRepository(CRUDBase[Bill, BillCreate, BillUpdate]):

    async def checking_in_list_one_plate(
        self, db: AsyncSession, bill_ids: list[int]
    ):
        plate_check = (
            select(Bill.plate).where(Bill.id.in_(bill_ids)).distinct()
        )
        result = await db.execute(plate_check)
        plates = result.scalars().all()

        if len(plates) == 0:
            raise exc.ServiceFailure(
                detail="No bills found for the given IDs",
                msg_code=MessageCodes.not_found,
            )
        elif len(plates) > 1:
            raise exc.ServiceFailure(
                detail="Bills have different plates",
                msg_code=MessageCodes.input_error,
            )
        return True

    async def get_bills_by_ids(
        self, db: AsyncSession, bill_ids: list[int]
    ) -> list[Bill]:
        """gets bills by ids with filter"""

        query = select(Bill).where(
            and_(
                Bill.id.in_(bill_ids),
                Bill.is_deleted == false(),
                Bill.status == StatusBill.unpaid,
                Bill.price.is_not(null()),
            )
        )

        result = await db.execute(query)
        bills = result.scalars().all()

        return bills

    async def sum_bills_by_id(
        self,
        db: AsyncSession,
        bill_payment: BillPaymentSchemaPOS | BillPaymentSchemaIPG,
    ) -> SumBillsByIdSchema:
        """gets a list of bills ID and checks and return the plate and the total amount"""

        id_list = bill_payment.bill_ids

        plate_check = select(Bill.plate).where(Bill.id.in_(id_list)).distinct()
        result = await db.execute(plate_check)
        plates = result.scalars().all()

        if len(plates) == 0:
            raise exc.ServiceFailure(
                detail="No bills found for the given IDs",
                msg_code=MessageCodes.not_found,
            )
        elif len(plates) > 1:
            raise exc.ServiceFailure(
                detail="Bills have different plates",
                msg_code=MessageCodes.input_error,
            )

        plate = plates[0]

        stmt = select(func.sum(Bill.price).label("total_price")).where(
            Bill.is_deleted == False,
            Bill.status == StatusBill.unpaid.value,
            Bill.price.is_not(None),
            Bill.id.in_(id_list),
        )

        result = await db.execute(stmt)
        total_price = result.scalar()

        if total_price is None:
            raise exc.ServiceFailure(
                detail="No valid bills found for payment",
                msg_code=MessageCodes.not_found,
            )

        return SumBillsByIdSchema(plate=plate, amount=total_price)

    @staticmethod
    async def payment_request_post(data, url: str) -> httpx.Response | None:

        try:
            response = await make_requests.make_request(
                method="POST",
                url=str(settings.PAYMENT_ADDRESS) + url,
                json=data,
                auth=BasicAuth(
                    username=settings.PAYMENT_USER_NAME,
                    password=settings.PAYMENT_PASSWORD,
                ),
            )

            return response
        except Exception as e:
            logger.error(f"Send request to Payment fail {e}")
            raise exc.InternalServiceError(
                f"can not connect to the payment",
                msg_code=MessageCodes.internal_error,
            )

    @staticmethod
    async def payment_request_get(params, url: str) -> httpx.Response | None:
        try:
            response = await make_requests.make_request(
                method="GET",
                url=str(settings.PAYMENT_ADDRESS) + url,
                params=params,
                auth=BasicAuth(
                    username=settings.PAYMENT_USER_NAME,
                    password=settings.PAYMENT_PASSWORD,
                ),
            )
            return response
        except Exception as e:
            logger.error(f"Send request to Payment fail {e}")
            raise exc.InternalServiceError(
                f"can not connect to the payment",
                msg_code=MessageCodes.internal_error,
            )


class TransactionRepository(
    CRUDBase[models.Transaction, TransactionCreate, TransactionUpdate]
):
    async def get_and_lock(
        self, db: AsyncSession, id_transaction: int, random_num: str
    ) -> models.Transaction:
        query = (
            select(self.model)
            .filter(
                *[
                    self.model.id == id_transaction,
                    self.model.transaction_number == random_num,
                    self.model.is_deleted == False,
                ]
            )
            .with_for_update()
        )
        return await self._first(db.scalars(query))

    async def get_transaction_by_rrn(
        self,
        db: AsyncSession,
        rrn: str,
    ) -> models.Transaction:
        return await self._first(
            db.scalars(
                select(self.model).filter(
                    *[
                        self.model.rrn == rrn,
                        self.model.is_deleted == False,
                    ]
                )
            )
        )


pay_repo = PaymentRepository(Bill)
transaction_repo = TransactionRepository(models.Transaction)
