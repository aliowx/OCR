from app.core import exceptions as exc

from fastapi.encoders import jsonable_encoder
from app.payment.repo import payment_repo
from app.bill.repo import bill_repo, payment_bill_repo
from app.utils import PaginatedContent, MessageCodes
from app.payment.schemas import payment as paymentSchemas


async def create_payment_by_ids(db, ids: list[int], pay: bool = False):

    bills = await bill_repo.get_all_by_ids(db, ids=ids)

    if not bills:
        raise exc.ServiceFailure(
            detail=f"bill not exist", msg_code=MessageCodes.not_found
        )

    total_price = 0

    total_price = sum(bill.price for bill in bills if bill.price)

    payment = None
    if pay:
        payment = await payment_repo.create(
            db, obj_in=paymentSchemas.PaymentCreate(price=total_price)
        )

        for bill in bills:
            await payment_bill_repo.create(
                db,
                obj_in=paymentSchemas.PaymentBillCreate(
                    bill_id=bill.id, payment_id=payment.id
                ),
            )

    return jsonable_encoder(bills), total_price, payment
