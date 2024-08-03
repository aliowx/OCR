import logging
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas, utils
from app.api import deps
from app.api.services import records_services
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated
from cache.redis import redis_connect_async


logger = logging.getLogger(__name__)
namespace = "records"
router = APIRouter()


@router.get("/")
async def read_records(
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
    record_in: schemas.ParamsRecord = Depends(),
    asc: bool = False,
) -> APIResponseType[schemas.GetRecords]:
    """
    All record
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    records = await records_services.calculator_price(db, params=record_in)

    return APIResponse(records)


@router.post("/")
async def create_record(
    *,
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
    record_in: schemas.RecordCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.RecordCreate]:
    """
    Create new item.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    record = await crud.record.create(db=db, obj_in=record_in)
    return APIResponse(record)


@router.get("/{id}")
async def read_record(
    *,
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
    id: int,
) -> APIResponseType[schemas.Record]:
    """
    Get record by ID.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    record = await crud.record.get(db=db, id=id)
    if not record:
        exc.ServiceFailure(
            detail="Record Not Found", msg_code=utils.MessageCodes.not_found
        )
    return APIResponse(record)


@router.put("/")
async def update_record(
    db: AsyncSession = Depends(deps.get_db_async),
    *,
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
    id_record: int,
    params: schemas.RecordUpdate,
) -> APIResponseType[schemas.Record]:
    """
    update status record .
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    record = await crud.record.get(db=db, id=id_record)
    if not record:
        exc.ServiceFailure(
            detail="Record Not Found", msg_code=utils.MessageCodes.not_found
        )
    record_update = await crud.record.update(db, db_obj=record, obj_in=params)
    return APIResponse(record_update)


@router.websocket("/records")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = await redis_connect_async(240)  # 3 mins
    async with connection.pubsub() as channel:
        await channel.subscribe("records:1")
        try:
            while True:
                data = await channel.get_message(
                    ignore_subscribe_messages=True, timeout=240
                )
                # data = await websocket.receive_text()
                if data and "data" in data:
                    print(data["data"])
                    await websocket.send_text(data["data"])
        except:
            channel.unsubscribe("records:1")
