import pytest
from fastapi.encoders import jsonable_encoder
from app import crud
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.schemas import UserCreate
import base64
from app.core.config import settings
from app.main import app
from fastapi.security import OAuth2PasswordRequestForm
from tests.utils.utils import random_lower_string, random_username


transport = ASGITransport(app=app)
client = AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestUser:
    async def test_login_user(self, create_super_user_test,db):
        assert db
        assert create_super_user_test

        data_user = OAuth2PasswordRequestForm(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
        )
        form_data_user = {
            "username": data_user.username,
            "password": data_user.password,
        }
        user_login = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/user/login",
            data=form_data_user,
        )
        assert "access_token" in user_login.json()
        assert "token_type" in user_login.json()

    async def test_create_user(self, create_super_user_test, db):
        assert db
        assert create_super_user_test

        data_user = OAuth2PasswordRequestForm(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
        )
        form_data_user = {
            "username": data_user.username,
            "password": data_user.password,
        }
        user_login = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/user/login",
            data=form_data_user,
        )

        user_in = UserCreate(username=random_lower_string(), password=random_lower_string())
        user_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/user/",
            json=user_in.model_dump(),
            headers={
                "Authorization": f'{user_login.json()["token_type"]} {user_login.json()["access_token"]}'
            },
        )
        assert user_create.status_code == 200
        assert user_create.json()["content"]["username"] == user_in.username

    async def test_get_user(self, create_super_user_test,db):
        assert db
        assert create_super_user_test

        data_user = OAuth2PasswordRequestForm(
            username=settings.TEST_FIRST_SUPERUSER,
            password=settings.TEST_FIRST_SUPERUSER_PASSWORD,
        )
        form_data_user = {
            "username": data_user.username,
            "password": data_user.password,
        }
        user_login = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/user/login",
            data=form_data_user,
        )

        user_in = UserCreate(username=random_lower_string(), password=random_lower_string())
        user_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/user/",
            json=user_in.model_dump(),
            headers={
                "Authorization": f'{user_login.json()["token_type"]} {user_login.json()["access_token"]}'
            },
        )
        user_get = await client.get(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/user/{user_create.json()["content"]["id"]}",
            headers={
                "Authorization": f'{user_login.json()["token_type"]} {user_login.json()["access_token"]}'
            },
        )

        assert user_get.status_code == 200
        assert user_create.json()["content"]["username"] == user_get.json()["content"]["username"]
