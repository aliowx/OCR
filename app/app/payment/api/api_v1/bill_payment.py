import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.payment.schemas.payment import (
    BillPaymentSchema,
    PaymentReportInput,
    MakePaymentRequest,
    PaymentUrlEndpoint,
    MakePaymentResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    _PaymentStatus,
)

from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType
from app.payment.repo import pay_repo
from app.utils import PaginatedContent, MessageCodes
from app.bill.schemas import bill as billSchemas
from app.bill.services import bill as servicesBill
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Any


router = APIRouter()
namespace = "pay"
logger = logging.getLogger(__name__)


@router.post("/")
async def pay_bills_by_id(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    params: BillPaymentSchema,
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[Any]:
    """
    pay bill by bill id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    pay_info = await pay_repo.sum_bills_by_id(db, params)

    data = MakePaymentRequest(
        amount=pay_info.amount,
        mobile=pay_info.plate,
        terminal=params.serial_number,
        additional_data={"time": str(datetime.now()),
                         "plate":pay_info.plate},
    )

    response = await pay_repo.payment_request_post(
        data=data.model_dump(), url=PaymentUrlEndpoint.make
    )

    if response.status_code != 200:
        logger.error(
            f"Payment failed., {response.status_code = }, {response.text = }"
        )
        raise exc.InternalServiceError(
            msg_code=MessageCodes.unsuccessfully_pay
        )
    response_json: dict[str, Any] = response.json()
    response = MakePaymentResponse(**response_json["content"])

    data = VerifyPaymentRequest(order_id=response.order_id)
    for i in range(50):
        response = await pay_repo.payment_request_post(
            data=data.model_dump(), url=PaymentUrlEndpoint.verify
        )
        if (
            response.status_code <= 500
            and response.json()["content"]["status"]
            != _PaymentStatus.SentToPos
        ):
            break
        await asyncio.sleep(1)
    response_json = response.json()
    if (
        response.status_code != 200
        or response_json["content"]["status"] != _PaymentStatus.Verified
        or response_json["content"]["amount"] != pay_info.amount
    ):
        logger.error(
            f"Payment failed., {response.status_code = }, {response.text = }"
        )
        raise exc.InternalServiceError(
            msg_code=MessageCodes.unsuccessfully_pay
        )

    bills_update = []
    response = VerifyPaymentResponse(**response_json["content"])

    for bill_id in params.bill_ids:
        bills_update.append(
            billSchemas.BillUpdate(
                id=bill_id,
                rrn_number=response.reference_number,
                time_paid=datetime.now(),
                status=billSchemas.StatusBill.paid,
            )
        )
    result, msg_code = await servicesBill.update_multi_bill(
        db, bills_update=bills_update
    )

    return APIResponse(data=result, msg_code=16)


@router.get("/payments")
async def read_payments(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    report_input: PaymentReportInput = Depends(),
    skip: int = Query(0),
    limit: int = Query(100),
    get_total_count: bool = Query(False),
):
    data = {
        **report_input.dict(exclude_none=True),
        "skip": skip,
        "limit": limit,
        "get_total_count": get_total_count,
    }

    response = await pay_repo.payment_request_get(
        params=data, url=PaymentUrlEndpoint.reports
    )

    return response.json()
