import pytest
from fastapi.encoders import jsonable_encoder
from app import crud
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ImageCreateBase64
import base64
from app.core.config import settings
from app.main import app


transport = ASGITransport(app=app)
client = AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestImage:
    async def test_create_image(self):
        image_data = ImageCreateBase64(
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
        )
        response = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/images/",
            json=image_data.model_dump(),
        )

        assert response.status_code == 200

    # async def test_get_image(self, client):
    #     image_data = ImageCreateBase64(
    #         image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
    #     )
    #     image_create = await client.post(
    #         f"{settings.SUB_PATH}{settings.API_V1_STR}/images/",
    #         json=image_data.model_dump(),
    #     )
    #     assert image_create.status_code == 200

    #     id = image_create.json()["content"]["id"]

    #     image_get = await client.get(
    #         f"{settings.SUB_PATH}{settings.API_V1_STR}/images/{id}",
    #         headers={"accept": "application/json"},
    #     )
    #     print(image_get.json())
    #     assert image_get.status_code == 200
