import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.parking.repo import zone_repo
from app.parking.schemas import ZoneCreate, ZonePramsFilters
from app.parking.services import zone as zone_services
from tests.utils.utils import random_lower_string
from app.parking.schemas.equipment import EquipmentCreate, ReadEquipmentsFilter
from app.models.base import EquipmentStatus, EquipmentType
import random


@pytest.mark.asyncio
class TestZone:
    async def test_create_zone(self, db: AsyncSession):
        zone_in = ZoneCreate(
            name=random_lower_string(),
            floor_name=random_lower_string(),
            floor_number=random.randint(1, 10),
        )
        zone = await zone_services.create_zone(
            db,
            zone_input=zone_in,
        )

        assert zone.name == zone_in.name
        assert zone.floor_number == zone_in.floor_number
        assert zone.floor_name == zone_in.floor_name

    async def test_get_multi_with_filters_zone(self, db: AsyncSession):
        zone_in = ZoneCreate(
            name=random_lower_string(),
            floor_name=random_lower_string(),
            floor_number=random.randint(1, 10),
        )
        zone_create = await zone_services.create_zone(
            db,
            zone_input=zone_in,
        )

        zones, total_count = await zone_repo.get_multi_by_filter(
            db,
            params=ZonePramsFilters(
                input_name_zone=zone_in.name,
                input_name_floor=zone_in.floor_name,
                input_number_floor=zone_in.floor_number,
            ),
        )
        for zone in zones:
            assert zone.name == zone_create.name
            assert zone.floor_number == zone_create.floor_number
            assert zone.floor_name == zone_create.floor_name
