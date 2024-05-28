import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.security import verify_password
from app.schemas.user import UserCreate, UserUpdate
from tests.utils.utils import random_lower_string, random_username


@pytest.mark.asyncio
class TestUser:
    async def test_create_user(self, db: AsyncSession) -> None:
        username = random_username()
        password = random_lower_string()
        user_in = UserCreate(username=username, password=password)
        user = await crud.user.create(db, obj_in=user_in)
        assert user.username == username
        assert hasattr(user, "hashed_password")

    async def test_authenticate_user(self, db: AsyncSession) -> None:
        username = random_username()
        password = random_lower_string()
        user_in = UserCreate(username=username, password=password)
        user = await crud.user.create(db, obj_in=user_in)
        authenticated_user = await crud.user.authenticate(
            db, username=username, password=password
        )
        assert authenticated_user
        assert user.username == authenticated_user.username

    async def test_not_authenticate_user(self, db: AsyncSession) -> None:
        username = random_username()
        password = random_lower_string()
        user = await crud.user.authenticate(
            db, username=username, password=password
        )
        assert user is None

    async def test_check_if_user_is_active(self, db: AsyncSession) -> None:
        username = random_username()
        password = random_lower_string()
        user_in = UserCreate(username=username, password=password)
        user = await crud.user.create(db, obj_in=user_in)
        is_active = crud.user.is_active(user)
        assert is_active is True

    async def test_check_if_user_is_active_inactive(
        self, db: AsyncSession
    ) -> None:
        username = random_username()
        password = random_lower_string()
        user_in = UserCreate(
            username=username, password=password, disabled=True
        )
        user = await crud.user.create(db, obj_in=user_in)
        is_active = crud.user.is_active(user)
        assert is_active

    async def test_check_if_user_is_superuser(self, db: AsyncSession) -> None:
        username = random_username()
        password = random_lower_string()
        user_in = UserCreate(
            username=username, password=password, is_superuser=True
        )
        user = await crud.user.create(db, obj_in=user_in)
        is_superuser = crud.user.is_superuser(user)
        assert is_superuser is True

    async def test_check_if_user_is_superuser_normal_user(
        self, db: AsyncSession
    ) -> None:
        username = random_username()
        password = random_lower_string()
        user_in = UserCreate(username=username, password=password)
        user = await crud.user.create(db, obj_in=user_in)
        is_superuser = crud.user.is_superuser(user)
        assert is_superuser is False

    async def test_get_user(self, db: AsyncSession) -> None:
        password = random_lower_string()
        username = random_username()
        user_in = UserCreate(
            username=username, password=password, is_superuser=True
        )
        user = await crud.user.create(db, obj_in=user_in)
        user_2 = await crud.user.get(db, id=user.id)
        assert user_2
        assert user.username == user_2.username
        assert jsonable_encoder(user) == jsonable_encoder(user_2)

    async def test_update_user(self, db: AsyncSession) -> None:
        password = random_lower_string()
        username = random_username()
        user_in = UserCreate(
            username=username, password=password, is_superuser=True
        )
        user = await crud.user.create(db, obj_in=user_in)
        new_password = random_lower_string()
        user_in_update = UserUpdate(password=new_password, is_superuser=True)
        await crud.user.update(db, db_obj=user, obj_in=user_in_update)
        user_2 = await crud.user.get(db, id=user.id)
        assert user_2
        assert user.username == user_2.username
        assert verify_password(new_password, user_2.hashed_password)
