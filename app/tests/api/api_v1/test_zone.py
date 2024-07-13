import pytest
from httpx import AsyncClient, ASGITransport
from app.core.config import settings
from app.main import app
from app.parking.schemas.zone import ZoneCreate
from tests.utils.utils import random_lower_string

transport = ASGITransport(app=app)
client = AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestZone:
    async def test_create_zone(self,login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

    async def test_get_zone(self,login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        zone_get = await client.get(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/{zone_create.json()['content']["id"]}",
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_get.status_code == 200
        assert zone_get.json()["content"]["name"] == zone_create.json()["content"]["name"]