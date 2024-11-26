import logging
from fastapi import APIRouter, Depends, UploadFile, File, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, utils
from app.notifications import schemas
from app.notifications.repo import notifications_repo
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, PaginatedContent
from app.notifications.services import notifications as ServiceNotifications
from cache.redis import redis_connect_async
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Any
import rapidjson


router = APIRouter()
namespace = "notifications"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_notifications(
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
    params: schemas.ParamsNotifications = Depends(),
) -> APIResponseType[PaginatedContent[list[schemas.Notifications]]]:
    """
    Retrieve notifications.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    notifications, total_count = (
        await ServiceNotifications.get_multi_notifications_by_filter(
            db, params=params
        )
    )
    return APIResponse(
        PaginatedContent(
            data=notifications,
            total_count=total_count,
            size=params.size,
            page=params.page,
        )
    )


@router.post("/")
async def create_notifications(
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
    notifications_in: schemas.NotificationsCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Notifications]:
    """
    Create new notifications.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    notifications = await notifications_repo.create(
        db, obj_in=notifications_in.model_dump()
    )
    return APIResponse(notifications)


@router.get("/{id}")
async def read_notifications_by_id(
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
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    id: int,
) -> APIResponseType[schemas.Notifications]:
    """
    Get a specific notifications by id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    notifications = await notifications_repo.get(db, id=id)
    if not notifications:
        raise exc.ServiceFailure(
            detail="notifications not found",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(notifications)


@router.delete("/{id}")
async def delete_notifications(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                ]
            )
        ),
    ],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    id: int,
) -> APIResponseType[schemas.Notifications]:
    """
    delete notifications.
    user access to this [ ADMINISTRATOR ]
    """
    notifications = await notifications_repo.get(db, id=id)
    if not notifications:
        raise exc.ServiceFailure(
            detail="notifications not found",
            msg_code=utils.MessageCodes.not_found,
        )
    del_notifications = await notifications_repo.remove(
        db, id=notifications.id, commit=True
    )
    return APIResponse(del_notifications)


@router.put("/{id}")
async def update_notifications(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
    notifications_in: schemas.NotificationsUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Notifications]:
    """
    Update a notifications.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    notifications = await notifications_repo.get(db, id=id)
    if not notifications:
        raise exc.ServiceFailure(
            detail="The notifications does't exist in the system",
            msg_code=utils.MessageCodes.not_found,
        )
    notifications = await notifications_repo.update(
        db, db_obj=notifications, obj_in=notifications_in.model_dump()
    )
    return APIResponse(notifications)


@router.websocket("/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = await redis_connect_async(240)  # 3 mins
    async with connection.pubsub() as channel:
        await channel.subscribe("notifications")
        try:
            while True:
                data = await channel.get_message(
                    ignore_subscribe_messages=True, timeout=240
                )
                # data = await websocket.receive_text()
                if data and "data" in data:
                    try:
                        # Decode JSON data if it’s a JSON string
                        message = rapidjson.loads(data["data"])
                        await websocket.send_json(
                            message
                        )  # Send JSON data directly to WebSocket
                    except (rapidjson.JSONDecodeError, TypeError) as e:
                        print(f"Error decoding message: {e}")
                        await websocket.send_text(
                            "Error: Invalid message format."
                        )
        except Exception as e:
            print(f"Exception in WebSocket connection: {e}")
            await channel.unsubscribe("notifications")
        finally:
            await websocket.close()
