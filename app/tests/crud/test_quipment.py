import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import ImageCreateBase64
from app.parking.repo import equipment_repo
from app.parking.schemas import ZoneCreate
from app.parking.services import zone as zone_services
from tests.utils.utils import random_lower_string
from app.parking.schemas.equipment import EquipmentCreate, ReadEquipmentsFilter
from app.models.base import EquipmentStatus, EquipmentType
import random


@pytest.mark.asyncio
class TestEquipment:
    async def test_create_quipment(self, db: AsyncSession):
        image_in = ImageCreateBase64(
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
        )
        image = await crud.image.create_base64(db=db, obj_in=image_in)
        zone_in = ZoneCreate(
            name=random_lower_string(),
            floor_name=random_lower_string(),
            floor_number=random.randint(1, 10),
        )
        zone = await zone_services.create_zone(
            db,
            zone_input=zone_in,
        )
        equipment_in = EquipmentCreate(
            equipment_status=EquipmentStatus.HEALTHY,
            equipment_type=EquipmentType.SENSOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        equipment = await equipment_repo.create(db, obj_in=equipment_in)

        assert equipment.serial_number == equipment_in.serial_number
        assert equipment.zone_id == zone.id
        assert equipment.image_id == image.id

    async def test_get_quipment(self, db: AsyncSession):
        image_in = ImageCreateBase64(
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
        )
        image = await crud.image.create_base64(db=db, obj_in=image_in)
        zone_in = ZoneCreate(
            name=random_lower_string(),
            floor_name=random_lower_string(),
            floor_number=random.randint(1, 10),
        )
        zone = await zone_services.create_zone(
            db,
            zone_input=zone_in,
        )
        equipment_in = EquipmentCreate(
            equipment_status=EquipmentStatus.DISCONNECTED,
            equipment_type=EquipmentType.DISPLAY,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)
        equipment_get = await equipment_repo.get(db, id=equipment_create.id)

        assert equipment_get
        assert jsonable_encoder(equipment_create) == jsonable_encoder(
            equipment_get
        )

    async def test_get_multi_with_filters_quipment(self, db: AsyncSession):
        image_in = ImageCreateBase64(
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
        )
        image = await crud.image.create_base64(db=db, obj_in=image_in)
        zone_in = ZoneCreate(
            name=random_lower_string(),
            floor_name=random_lower_string(),
            floor_number=random.randint(1, 10),
        )
        zone = await zone_services.create_zone(
            db,
            zone_input=zone_in,
        )
        equipment_in = EquipmentCreate(
            equipment_status=EquipmentStatus.BROKEN,
            equipment_type=EquipmentType.CAMERA_ENTRANCE_DOOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)
        # function get_multi_with_filters return [equipment,total_ccount]
        equipments_get, totla_count = (
            await equipment_repo.get_multi_with_filters(
                db,
                filters=ReadEquipmentsFilter(
                    serial_number__eq=equipment_in.serial_number,
                    equipment_status__eq=equipment_in.equipment_status,
                    equipment_type__eq=equipment_in.equipment_type,
                ),
            )
        )
        for equipment in equipments_get:
            assert equipment.serial_number == equipment_create.serial_number
            assert (
                equipment.equipment_status == equipment_create.equipment_status
            )
            assert equipment.equipment_type == equipment_create.equipment_type

    async def test_get_quipment_with_serial_number(self, db: AsyncSession):
        image_in = ImageCreateBase64(
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdjcBOp+A8AA0gB0kAdSDgAAAAASUVORK5CYII="
        )
        image = await crud.image.create_base64(db=db, obj_in=image_in)
        zone_in = ZoneCreate(
            name=random_lower_string(),
            floor_name=random_lower_string(),
            floor_number=random.randint(1, 10),
        )
        zone = await zone_services.create_zone(
            db,
            zone_input=zone_in,
        )
        equipment_in = EquipmentCreate(
            equipment_status=EquipmentStatus.DISCONNECTED,
            equipment_type=EquipmentType.ERS,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)

        equipment_get = await equipment_repo.one_equipment(
            db, serial_number=equipment_in.serial_number
        )

        assert equipment_get
        assert equipment_get.serial_number == equipment_create.serial_number
