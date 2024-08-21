import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import ImageCreateBase64
import base64


@pytest.mark.asyncio
class TestImage:
    async def test_create_image(self, db: AsyncSession):

        image_in = ImageCreateBase64(
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
        )
        image = await crud.image.create_base64(db=db, obj_in=image_in)

        assert image
        assert image_in.image == image.image

    async def test_get_image(self, db: AsyncSession):

        # base 64 image 1px
        image_in = ImageCreateBase64(
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
        )
        image_create = await crud.image.create_base64(db=db, obj_in=image_in)
        image_get = await crud.image.get(db, id=image_create.id)

        assert image_get.id
        assert image_create.image == base64.b64encode(image_get.image).decode()
