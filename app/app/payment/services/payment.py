from app.payment.repo import pay_repo
from sqlalchemy.ext.asyncio import AsyncSession
from app.payment import schemas
from datetime import datetime, UTC
from app.core import exceptions
from typing import Any
from app.utils import MessageCodes
from app.bill.schemas.bill import BillUpdate, StatusBill
from app.bill.services import bill
import asyncio


async def pay_bill_by_pos(
    db: AsyncSession,
    params: schemas.BillPaymentSchemaPOS,
):
    pay_info = await pay_repo.sum_bills_by_id(db, params)
    data = schemas.MakePaymentRequest(
        amount=pay_info.amount,
        mobile=pay_info.plate,
        terminal=params.serial_number,
        additional_data=(
            {"time": str(datetime.now()), "plate": pay_info.plate}
        ),
    )

    response = await pay_repo.payment_request_post(
        data=data.model_dump(), url=schemas.PaymentUrlEndpoint.make
    )

    if response.status_code != 200:
        raise exceptions.InternalServiceError(
            msg_code=MessageCodes.unsuccessfully_pay
        )
    response_json: dict[str, Any] = response.json()
    response = schemas.MakePaymentResponse(**response_json["content"])

    data = schemas.VerifyPaymentRequest(order_id=response.order_id)
    for i in range(50):
        response = await pay_repo.payment_request_post(
            data=data.model_dump(), url=schemas.PaymentUrlEndpoint.verify
        )
        if (
            response.status_code <= 500
            and response.json()["content"]["status"]
            != schemas._PaymentStatus.SentToPos
        ):
            break
        await asyncio.sleep(1)
    response_json = response.json()
    if (
        response.status_code != 200
        or response_json["content"]["status"]
        != schemas._PaymentStatus.Verified
        or response_json["content"]["amount"] != pay_info.amount
    ):
        raise exceptions.InternalServiceError(
            msg_code=MessageCodes.unsuccessfully_pay
        )
    bills_update = []
    response = schemas.VerifyPaymentResponse(**response_json["content"])

    for bill_id in params.bill_ids:
        bills_update.append(
            BillUpdate(
                id=bill_id,
                rrn_number=response.reference_number,
                time_paid=datetime.now(UTC).replace(tzinfo=None),
                status=StatusBill.paid,
            )
        )
    result, msg_code = await bill.update_multi_bill(
        db, bills_update=bills_update
    )

    return result
