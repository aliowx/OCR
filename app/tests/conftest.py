import asyncio
from typing import AsyncGenerator, Generator
from app.models.base import EquipmentType, EquipmentStatus
from tests.utils.utils import random_lower_string
from app.parking.schemas.zone import ZoneCreate
import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_db_async
from app.core.config import settings
from app.db import Base
from app.main import app
from app.users.schemas import UserCreate,ZoneCreate, EquipmentCreate, SpotCreate
from app import crud

engine = create_async_engine(
    str(settings.TEST_SQLALCHEMY_DATABASE_URI), pool_pre_ping=True
)

async_session_local = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db_async() -> AsyncGenerator:
    async with async_session_local() as db:
        yield db
        await db.commit()


app.dependency_overrides[get_db_async] = override_get_db_async


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:  # noqa: indirect usage
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db() -> AsyncSession:
    async_engine = engine
    async_session = async_session_local

    async with async_session() as session:
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        yield session

    await async_engine.dispose()


@pytest_asyncio.fixture(scope="module")
async def client() -> AsyncClient:
    async with asyncpg.create_pool(
        dsn=f"postgresql://{settings.TEST_DSN_POSTGRES_NAME}:{settings.TEST_DSN_POSTGRES_PASSWORD}@{settings.TEST_DSN_POSTGRES_IP}:{settings.TEST_DSN_POSTGRES_PORT}/{settings.TEST_DSN_POSTGRES_DB_NAME}"
    ) as pool:
        async with AsyncClient(app=app, base_url="http://test") as client:
            client.db = pool
            try:
                yield client
            except SQLAlchemyError as e:
                await pool.rollback()  # Rollback the database transaction
                raise e


@pytest_asyncio.fixture(scope="session")
async def create_super_user_test(db: AsyncSession):
    username = settings.TEST_FIRST_SUPERUSER
    password = settings.TEST_FIRST_SUPERUSER_PASSWORD
    user_in = UserCreate(
        username=username,
        password=password,
        is_superuser=True,
        is_active=True,
        full_name="test@user.com",
    )
    user = await crud.user.create(db, obj_in=user_in)

    return user


@pytest_asyncio.fixture(scope="session")
async def login(db: AsyncSession):
    username = settings.TEST_FIRST_SUPERUSER
    password = settings.TEST_FIRST_SUPERUSER_PASSWORD

    user_in = UserCreate(
        username=username,
        password=password,
        is_superuser=True,
        is_active=True,
        full_name="test@user.com",
    )

    get_user = await crud.user.get_by_username(db, username=username)
    if not get_user:
        await crud.user.create(db, obj_in=user_in)

    data_user = OAuth2PasswordRequestForm(
        username=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
    )
    form_data_user = {
        "username": data_user.username,
        "password": data_user.password,
    }
    # this config pytest
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")

    user_login = await client.post(
        f"{settings.SUB_PATH}{settings.API_V1_STR}/user/login",
        data=form_data_user,
    )

    return {
        "access_token": user_login.json()["access_token"],
        "token_type": user_login.json()["token_type"],
    }



@pytest_asyncio.fixture(scope="module")
async def create_zone(
    client,
    login
):
    zone_in = ZoneCreate(
        name = random_lower_string(),
    )
    response = await client