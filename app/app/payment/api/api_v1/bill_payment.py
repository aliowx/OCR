import asyncio
import logging
from datetime import datetime, UTC
from app.core.config import settings
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status as StatusCode
from app.payment.schemas.payment import (
    BillPaymentSchemaPOS,
    BillPaymentSchemaIPG,
    PaymentReportInput,
    MakePaymentRequest,
    PaymentUrlEndpoint,
    MakePaymentResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    _PaymentStatus,
    _GatewayTypes,
    TransactionCreate,
    TransactionUpdate,
    CallBackCreate,
    CallBackUserCreate,
)
from app.bill.repo import bill_repo
from app.bill.schemas.bill import StatusBill, BillB2B
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType
from app.payment.repo import pay_repo, transaction_repo
from app.utils import PaginatedContent, MessageCodes
from app.bill.schemas import bill as billSchemas
from app.bill.services import bill as servicesBill
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Any
from fastapi.responses import RedirectResponse
from app import models
from sqlalchemy.exc import IntegrityError
from random import randint

router = APIRouter()
namespace = "pay"
logger = logging.getLogger(__name__)


@router.post("/pos")
async def pay_bills_by_id_pos(
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
    params: BillPaymentSchemaPOS,
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
        additional_data=(
            {"time": str(datetime.now()), "plate": pay_info.plate}
        ),
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
                time_paid=datetime.now(UTC).replace(tzinfo=None),
                status=billSchemas.StatusBill.paid,
            )
        )
    result, msg_code = await servicesBill.update_multi_bill(
        db, bills_update=bills_update
    )

    return APIResponse(data=result, msg_code=16)


# for payment switch
@router.get("/call-back/{transaction_id}")
async def pay_bills_by_id_ipg(
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
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    transaction_id: str,
) -> APIResponseType[Any]:
    """
    pay bill by bill id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    transaction_id_currect = transaction_id
    # check not verifyd with lock
    get_transaction = await transaction_repo.get_and_lock(
        db, id=transaction_id_currect
    )
    print(get_transaction)
    if not get_transaction:
        raise exc.ServiceFailure(
            detail="transaction not Fount",
            msg_code=MessageCodes.not_found,
        )

    if get_transaction.status == _PaymentStatus.Verified:
        get_transaction.status = _PaymentStatus.Verified
        return RedirectResponse(
            f"{get_transaction.callback_url}?amount={get_transaction.amount}&status={get_transaction.status}&transaction_id={transaction_id}",
            status_code=StatusCode.HTTP_303_SEE_OTHER,
        )

    if get_transaction.status == _PaymentStatus.created:
        data = VerifyPaymentRequest(order_id=get_transaction.order_id_b2b)
        response = await pay_repo.payment_request_post(
            data=data.model_dump(), url=PaymentUrlEndpoint.verify
        )
        response_json = response.json()
        if (
            response.status_code == 200
            or response_json["content"]["status"] == _PaymentStatus.Verified
            or response_json["content"]["amount"] == get_transaction.amount
        ):
            result, msg_code = await servicesBill.update_bills(
                db=db,
                bill_ids_in=get_transaction.bill_ids,
                rrn_number_in=get_transaction.rrn,
                time_paid_in=datetime.now(UTC).replace(tzinfo=None),
                status_in=billSchemas.StatusBill.paid,
            )
            get_transaction.status = _PaymentStatus.Verified
        else:
            get_transaction.status = _PaymentStatus.Failed

    if get_transaction.status == _PaymentStatus.Failed:
        get_transaction.status = _PaymentStatus.Failed

    update_transaction = await transaction_repo.update(
        db, db_obj=get_transaction
    )

    return RedirectResponse(
        f"{get_transaction.callback_url}?amount={update_transaction.amount}&status={update_transaction.status}&transaction_id={transaction_id}",
        status_code=StatusCode.HTTP_303_SEE_OTHER,
    )


@router.post("/pay-bill")
async def pay_bills_by_id_ipg(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.ITOLL,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
    *,
    params: CallBackCreate,
) -> APIResponseType[Any]:
    """
    pay bill by bill id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , ITOLL ]
    """

    checking_plate = await pay_repo.checking_in_list_one_plate(
        db, params.bill_ids
    )
    if (
        params.rrn is None
        or params.rrn <= 0
        or params.order_id_b2b <= 0
        or params.order_id_b2b is None
    ):
        raise exc.ServiceFailure(
            detail=f"checking order_id or rrn",
            msg_code=MessageCodes.operation_failed,
        )
    data = CallBackUserCreate(**params.__dict__, user_id=current_user.id)

    try:
        transaction = await transaction_repo.create(db, obj_in=data)
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            raise exc.ServiceFailure(
                detail=f"Order ID '{data.order_id_b2b}' already exists. Please use a unique order ID.",
                msg_code=MessageCodes.operation_failed,
            )
    before_paid = []
    update_bills = []
    total_amount = 0
    for bill_id in params.bill_ids:
        bill = await bill_repo.get(db, id=bill_id, for_update=True)
        total_amount += bill.price
        if bill.status == StatusBill.paid:
            before_paid.append(bill.id)
        else:
            update_bills.append(bill)

    if (
        update_bills != []
        and params.status == "paid"
        and total_amount == params.amount
    ):
        for bill in update_bills:
            bill.rrn_number = params.rrn_number
            bill.status = StatusBill.paid
            bill.time_paid = datetime.now(UTC).replace(tzinfo=None)
            update = await bill_repo.update(db, db_obj=bill)
    msg_code = 0
    if before_paid != []:
        msg_code = 14
    response = APIResponse(
        {
            "transaction_id": transaction.id,
            "bill_ids_before_paid": before_paid,
        },
        msg_code=msg_code,
    )
    if total_amount != params.amount:
        response.content.update(
            {"amount": params.amount, "total_amount_bills": total_amount}
        )
    return response


@router.post("/ipg")
async def pay_bills_by_id_ipg(
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
    params: BillPaymentSchemaIPG,
    db: AsyncSession = Depends(deps.get_db_async),
):
    """
    pay bill by bill id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    if (
        settings.GATEWAY_TYPE_PAY is None
        or settings.PROVIDER_PAY is None
        or settings.TERMINAL_PAY is None
        or params.call_back is None
        or params.phone_number is None
    ):
        raise exc.ServiceFailure(
            detail="set GATEWAY_TYPE_PAY or serial_number or TERMINAL_PAY or PROVIDER_PAY not None or phone_number or call_back",
            msg_code=MessageCodes.not_found,
        )
    pay_info = await pay_repo.sum_bills_by_id(db, params)

    craete_transaction = await transaction_repo.create(
        db,
        obj_in=TransactionCreate(
            bill_ids=params.bill_ids,
            amount=pay_info.amount,
            callback_url=params.call_back,
            status=_PaymentStatus.created,
        ),
    )

    # craete random int for transaction_id
    gen_int = lambda: randint(10000, 99999)
    data = MakePaymentRequest(
        gateway=settings.GATEWAY_TYPE_PAY,
        provider=settings.PROVIDER_PAY,
        terminal=settings.TERMINAL_PAY,
        username=settings.USER_NAME_PAY,
        password=settings.PASSWORD_USER_PAY,
        mobile=params.phone_number,
        callback_url=f"{settings.CALL_BACK_PAY}/{gen_int()}{craete_transaction.id}{gen_int()}",
        amount=pay_info.amount,
        # additional_data=(
        #     {"time": str(datetime.now()), "plate": pay_info.plate}
        # ),
    )
    print(data)
    response = await pay_repo.payment_request_post(
        data=data.model_dump(), url=PaymentUrlEndpoint.make
    )

    if response.status_code != 200:
        logger.error(
            f"Payment failed., {response.status_code = }, {response.json() = }, {response.text = }"
        )
        raise exc.InternalServiceError(
            msg_code=MessageCodes.unsuccessfully_pay
        )
    response_json = response.json()
    update_transaction = await transaction_repo.update(
        db,
        db_obj=craete_transaction,
        obj_in=TransactionUpdate(
            order_id_paymet_switch=response_json["content"]["order_id"]
        ),
    )

    return response_json


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


@router.get("/redirect/")
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
    status: str = Query(...),
    order_id: str = Query(...),
    amount: str = Query(...),
    call_back: str = Query(...),
):
    return RedirectResponse(
        f"{call_back}/status={status}?order_id={order_id}?amount={amount}"
    )


@router.get("/report_logs")
async def read_payments_logs(
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
    tracker_id: int,
    skip: int = Query(0),
    limit: int = Query(100),
    get_total_count: bool = Query(False),
):
    data = {
        "tracker_id": tracker_id,
        "skip": skip,
        "limit": limit,
        "get_total_count": get_total_count,
    }

    response = await pay_repo.payment_request_get(
        params=data, url=PaymentUrlEndpoint.reports_log
    )

    return response.json()
