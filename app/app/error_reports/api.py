import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, utils
from app.error_reports import schemas
from app.error_reports.repo import error_repo
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, PaginatedContent

from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "error"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_error(
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
    params: schemas.ParamsError = Depends(),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[PaginatedContent[list[schemas.Error]]]:
    """
    Retrieve error.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    errors, total_count = await error_repo.get_multi_by_filter(
        db, params=params
    )
    return APIResponse(
        PaginatedContent(
            data=errors,
            total_count=total_count,
            size=params.size,
            page=params.page,
        )
    )


@router.post("/")
async def create_error(
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
    error_in: schemas.ErrorCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Error]:
    """
    Create new error.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    error = await error_repo.create(db, obj_in=error_in)
    return APIResponse(error)


@router.get("/{id}")
async def read_error_by_id(
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
) -> APIResponseType[schemas.Error]:
    """
    Get a specific error by id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    error = await error_repo.get(db, id=id)
    if not error:
        raise exc.ServiceFailure(
            detail="error not found",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(error)


@router.delete("/{id}")
async def delete_error(
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
) -> APIResponseType[schemas.Error]:
    """
    delete error.
    user access to this [ ADMINISTRATOR ]
    """
    user = await error_repo.get(db, id=id)
    if not user:
        raise exc.ServiceFailure(
            detail="error not found",
            msg_code=utils.MessageCodes.not_found,
        )
    del_user = await error_repo.remove(db, id=user.id, commit=True)
    return APIResponse(del_user)


@router.put("/{id}")
async def update_user(
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
    error_in: schemas.ErrorUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Error]:
    """
    Update a error.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    error = await error_repo.get(db, id=id)
    if not error:
        raise exc.ServiceFailure(
            detail="The error does't exist in the system",
            msg_code=utils.MessageCodes.not_found,
        )
    error = await error_repo.update(db, db_obj=error, obj_in=error_in)
    return APIResponse(error)
