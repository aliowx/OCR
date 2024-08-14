import pytest
from httpx import AsyncClient, ASGITransport
from app.core.config import settings
from app.main import app
from app.parking.schemas.equipment import EquipmentCreate, EquipmentUpdate
from app.parking.schemas.zone import ZoneCreate
from app.models.base import EquipmentType, EquipmentStatus
from tests.utils.utils import random_lower_string

transport = ASGITransport(app=app)
client = AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestEquipment:
    async def test_create_equipment_camera_spot(self,login):
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
        assert equipment_create.json()["content"]["serial_number"] == equipment_in.serial_number

    async def test_create_equipment_camera_zone(self,login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.CAMERA_ENTRANCE_DOOR,
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
        assert equipment_create.json()["content"]["serial_number"] == equipment_in.serial_number

    async def test_create_equipment_disply(self,login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.DISPLAY,
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
        assert equipment_create.json()["content"]["serial_number"] == equipment_in.serial_number


    async def test_create_equipment_ers(self,login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.ERS,
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
        assert equipment_create.json()["content"]["serial_number"] == equipment_in.serial_number


    async def test_create_equipment_roadblock(self,login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.ROADBLOCK,
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
        assert equipment_create.json()["content"]["serial_number"] == equipment_in.serial_number

    async def test_update_equipment(self, login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.ROADBLOCK,
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

        equipment_update_in = EquipmentUpdate(
            equipment_type=EquipmentType.SENSOR,
            equipment_status=EquipmentStatus.BROKEN,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone_create.json()["content"]["id"],
        )
        equipment_update = await client.put(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/equipment/{equipment_create.json()["content"]["id"]}",
            json=equipment_update_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert equipment_update.status_code == 200
        assert equipment_update.json()["content"]["equipment_type"] != equipment_create.json()["content"]["equipment_type"]


    async def test_delete_equipment(self, login):
        zone_in = ZoneCreate(name=random_lower_string())

        zone_create = await client.post(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/zone/",
            json=zone_in.model_dump(),
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert zone_create.status_code == 200

        equipment_in = EquipmentCreate(
            equipment_type=EquipmentType.ROADBLOCK,
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

        
        equipment_delete = await client.delete(
            f"{settings.SUB_PATH}{settings.API_V1_STR}/equipment/{equipment_create.json()["content"]["id"]}",
            headers={"Authorization": f"{login["token_type"]} {login["access_token"]}"}
        )

        assert equipment_delete.status_code == 200
