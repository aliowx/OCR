import logging
from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app import crud
from app import exceptions as exc
from app import models, schemas, utils
from app.api import deps
from app.core import security
from app.core.config import settings
from app.utils import APIResponse, APIResponseType
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS

router = APIRouter()
namespace = "user"
logger = logging.getLogger(__name__)


@router.post("/login/access-token")
async def login_access_token(
    request: Request,
    db: AsyncSession = Depends(deps.get_db_async),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await crud.user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise exc.InternalServiceError(
            status_code=401,
            detail="Incorrect username or password",
            msg_code=utils.MessageCodes.incorrect_username_or_password,
        )
    elif not crud.user.is_active(user):
        raise exc.InternalServiceError(
            status_code=401,
            detail="Incorrect username or password",
            msg_code=utils.MessageCodes.incorrect_username_or_password,
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    return schemas.Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        token_type="bearer",
        # 'access_list' later used for user access control
        access_list=[route.name for route in request.app.routes],
    )


@router.get("/")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_users(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[list[schemas.User]]:
    """
    Retrieve users.
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return APIResponse(users)


@router.post("/")
@invalidate(namespace=namespace)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.User]:
    """
    Create new user.
    """
    user = await crud.user.get_by_username(db, username=user_in.username)
    if user:
        raise exc.ServiceFailure(
            detail="The user with this username already exists in the system.",
            msg_code=utils.MessageCodes.bad_request,
        )
    user = await crud.user.create(db, obj_in=user_in)
    return APIResponse(user)


@router.get("/{user_id}")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[schemas.User]:
    """
    Get a specific user by id.
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise exc.ServiceFailure(
            detail="User not found",
            msg_code=utils.MessageCodes.not_found,
        )
    if user == current_user:
        return APIResponse(user)
    if not crud.user.is_superuser(current_user):
        raise exc.ServiceFailure(
            detail="The user doesn't have enough privileges",
            msg_code=utils.MessageCodes.bad_request,
        )
    return APIResponse(user)


@router.put("/{user_id}")
async def update_user(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.User]:
    """
    Update a user.
    """
    user = await crud.user.get(db, id=user_id)
    if not user:
        raise exc.ServiceFailure(
            detail="The user with this username does not exist in the system",
            msg_code=utils.MessageCodes.not_found,
        )
    user = await crud.user.update(db, db_obj=user, obj_in=user_in)
    return APIResponse(user)
