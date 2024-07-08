import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.parking.repo import parking_repo
from app.parking.schemas import ParkingCreate
from tests.utils.utils import random_lower_string, random_username
import random


@pytest.mark.asyncio
class TestParking:
    async def test_create_parking(self, db: AsyncSession):
        parking_in = ParkingCreate(
            name=random_username(),
            brand_name=random_username(),
            floor_count=random.randint(1, 10),
        )
        parking = await parking_repo.create(db, obj_in=parking_in)

        assert parking.name == parking_in.name
        assert parking.brand_name == parking_in.brand_name
        assert parking.floor_count == parking_in.floor_count

    async def test_get_parking(self, db: AsyncSession):
        parking_in = ParkingCreate(
            name=random_username(),
            brand_name=random_username(),
            floor_count=random.randint(1, 10),
        )
        parking_create = await parking_repo.create(db, obj_in=parking_in)
        parking_get = await parking_repo.get(db, id=parking_create.id)

        assert parking_get
        assert parking_create.name == parking_get.name
        assert jsonable_encoder(parking_create) == jsonable_encoder(
            parking_get
        )
