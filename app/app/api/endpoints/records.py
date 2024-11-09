import logging
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from app import crud, models, schemas, utils
from app.api import deps
from app.api.services import records_services
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Optional, List
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
    *,
    record_in: schemas.ParamsRecord = Depends(),
    input_status_record: Optional[List[schemas.record.StatusRecord]] = Query(
        None
    ),
    input_camera_entrance_id: Optional[list[int]] = Query(None),
    input_camera_exit_id: Optional[list[int]] = Query(None),
) -> APIResponseType[schemas.GetRecords]:
    """
    All record
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    records = await records_services.get_multi_by_filters(
        db,
        params=record_in,
        input_status_record=input_status_record,
        input_camera_entrance_id=input_camera_entrance_id,
        input_camera_exit_id=input_camera_exit_id,
    )

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


@router.get("/get-events-by-record-id/")
async def get__events_by_record_id(
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
    record_id: int,
) -> APIResponseType[schemas.GetEvents]:
    """
    Get events by record_id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    record_exist = await crud.record.get(db, id=record_id)
    if not record_exist:
        raise exc.ServiceFailure(
            detail="record Not Found", msg_code=utils.MessageCodes.not_found
        )
    events, count = await records_services.get_events_by_record_id(
        db=db, record_id=record_id
    )
    if not events:
        raise exc.ServiceFailure(
            detail="event Not Found", msg_code=utils.MessageCodes.not_found
        )
    return APIResponse(schemas.GetEvents(items=events, all_items_count=count))


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


@router.post("/excel")
async def download_excel(
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
    current_user: models.User = Depends(deps.get_current_active_superuser),
    *,
    params: schemas.ParamsRecord = Depends(),
    input_status_record: Optional[list[schemas.record.StatusRecord]] = Query(
        None
    ),
    input_camera_entrance_id: Optional[list[int]] = Query(None),
    input_camera_exit_id: Optional[list[int]] = Query(None),
    input_excel_name: str = f"{datetime.now().date()}",
) -> StreamingResponse:
    """
    excel plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    return await records_services.gen_excel_record(
        db,
        params=params,
        input_status_record=input_status_record,
        input_camera_entrance_id=input_camera_entrance_id,
        input_camera_exit_id=input_camera_exit_id,
        input_excel_name=input_excel_name,
    )
