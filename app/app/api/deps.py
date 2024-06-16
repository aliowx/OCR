from typing import Annotated, AsyncGenerator, Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OAuth2PasswordBearer,
)
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas, utils
from app.core import exceptions as exc
from app.core import security
from app.core.config import AuthMethod, settings
from app.db.session import AsyncSessionLocal, SessionLocal


class APIOAuth2(OAuth2PasswordBearer):
    async def __call__(self, request: Request):
        authorization = request.headers.get("Authorization", "").lower()
        if "bearer" not in authorization:
            return None
        if AuthMethod.JWT not in settings.ALLOWED_AUTH_METHODS:
            raise exc.InternalServiceError(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Auth method not allowed",
                msg_code=utils.MessageCodes.forbidden,
            )
        return await super().__call__(request)


class APIBasicAuth(HTTPBasic):
    async def __call__(self, request: Request):
        authorization = request.headers.get("Authorization", "").lower()
        if "basic" not in authorization:
            return None
        if AuthMethod.BASIC not in settings.ALLOWED_AUTH_METHODS:
            raise exc.InternalServiceError(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Auth method not allowed",
                msg_code=utils.MessageCodes.forbidden,
            )
        return await super().__call__(request)


reusable_oauth2 = APIOAuth2(tokenUrl=f"{settings.API_V1_STR}/user/login")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


async def get_db_async() -> AsyncGenerator:
    """
    Dependency function that yields db sessions
    """
    async with AsyncSessionLocal() as db:
        yield db


def get_user_id_from_bearer_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
        return token_data.sub
    except (jwt.JWTError, ValidationError) as e:
        raise exc.InternalServiceError(
            status_code=401,
            detail="Could not validate credentials",
            msg_code=utils.MessageCodes.bad_request,
        ) from e


async def get_current_user(
    db: AsyncSession = Depends(get_db_async),
    token: str | None = Depends(reusable_oauth2),
    credentials: HTTPBasic | None = Depends(APIBasicAuth()),
) -> models.User:
    if token:
        user_id = get_user_id_from_bearer_token(token)
        user = await crud.user.get(db, id=user_id)
    elif credentials:
        user = await crud.user.authenticate_async(
            db, username=credentials.username, password=credentials.password
        )
    else:
        raise exc.InternalServiceError(
            status_code=401,
            detail="Not authenticated",
            msg_code=utils.MessageCodes.bad_request,
        )

    if not user:
        raise exc.InternalServiceError(
            status_code=401,
            detail="Auth user not found",
            msg_code=utils.MessageCodes.bad_request,
        )
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise exc.InternalServiceError(
            status_code=401,
            detail="Inactive user",
            msg_code=utils.MessageCodes.inactive_user,
        )
    return current_user


async def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise exc.InternalServiceError(
            status_code=403,
            detail="The user doesn't have enough privileges",
            msg_code=utils.MessageCodes.bad_request,
        )
    return current_user


async def basic_auth_superuser(
    credentials: Annotated[HTTPBasicCredentials, Depends(HTTPBasic())],
    db: AsyncSession = Depends(get_db_async),
) -> str:
    """
    authenticate user with basic credentials
    """

    if settings.DEBUG:
        return credentials.username

    user = await crud.user.authenticate_async(
        db, username=credentials.username, password=credentials.password
    )
    if not user or not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user.username
