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

    # async def test_get_by_id_image(self, db: AsyncSession):
    #     image_in = ImageCreateBase64(
    #         image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
    #     )
    #     image_create = await crud.image.create_base64(db=db, obj_in=image_in)
    #     auth = (settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD)
    #     response = await client.get(
    #         f"{settings.SUB_PATH}{settings.API_V1_STR}/images/{image_create.id}",
    #         auth=auth,
    #         headers={"Content-Type": "application/json"},
    #     )

    #     assert response
