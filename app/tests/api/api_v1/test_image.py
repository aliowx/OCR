import pytest
from httpx import AsyncClient, ASGITransport
from app.schemas import ImageCreateBase64
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

    # async def test_get_image(self, login):
    #     image_data = ImageCreateBase64(
    #         image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
    #     )
    #     image_create = await client.post(
    #         f"{settings.SUB_PATH}{settings.API_V1_STR}/images/",
    #         json=image_data.model_dump(),
    #         headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}

    #     )
    #     assert image_create.status_code == 200

    #     image_get = await client.get(
    #         f"{settings.SUB_PATH}{settings.API_V1_STR}/images/{image_create.json()["content"]["id"]}",
    #         headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
    #     )
    #     assert image_get.status_code == 200
