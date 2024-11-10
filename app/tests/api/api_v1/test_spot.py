import pytest
from httpx import AsyncClient, ASGITransport
from app.core.config import settings
from app.main import app
from app.parking.schemas.equipment import EquipmentCreate
from app.parking.schemas.zone import ZoneCreate
from app.parking.schemas.spot import SpotCreate
from app.models.base import EquipmentType, EquipmentStatus
from tests.utils.utils import random_lower_string

transport = ASGITransport(app=app)
client = AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestSpot:
    async def test_create_spot(self,login):

        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.SENSOR,
            equipment_status=EquipmentStatus.HEALTHY,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone_create.json()["content"]["id"],
        )
        equipment_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/equipment/",
            json=equipment_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert equipment_create.status_code == 200

        spot_in = SpotCreate(
            name_spot=random_lower_string(),
            coordinates_rectangles=[{
                    "percent_rotation_rectangle_small": 90,
                    "percent_rotation_rectangle_big": 90,
                    "number_spot": 1,
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
            }],
            camera_serial=equipment_create.json()["content"]["serial_number"],
            zone_id=equipment_create.json()["content"]["zone_id"],
        )

        spot_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/spot/",
            json=spot_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert spot_create.status_code == 200


    async def test_update_status_spot(self,login):

        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.SENSOR,
            equipment_status=EquipmentStatus.HEALTHY,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone_create.json()["content"]["id"],
        )
        equipment_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/equipment/",
            json=equipment_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert equipment_create.status_code == 200

        spot_in = SpotCreate(
            name_spot=random_lower_string(),
            coordinates_rectangles=[{
                    "percent_rotation_rectangle_small": 90,
                    "percent_rotation_rectangle_big": 90,
                    "number_spot": 1,
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
            }],
            camera_serial=equipment_create.json()["content"]["serial_number"],
            zone_id=equipment_create.json()["content"]["zone_id"],
        )

        spot_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/spot/",
            json=spot_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )
        
        assert spot_create.status_code == 200