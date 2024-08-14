import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime
from app.schemas import ImageCreateBase64
from app.parking.repo import equipment_repo
from app.parking.schemas import spot as spotsSchemas
from app import crud
from app.parking.schemas import ZoneCreate
from app.parking.services import spot as spot_services
from app.parking.services import zone as zone_services
from tests.utils.utils import random_lower_string
from app.parking.schemas.equipment import EquipmentCreate
from app.parking.schemas.spot import Status as status_spot
from app.models.base import EquipmentStatus, EquipmentType
import random


@pytest.mark.asyncio
class TestSpot:
    async def test_create_spot(self, db: AsyncSession):
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
            equipment_type=EquipmentType.SENSOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)

        spot_in = spotsSchemas.SpotCreate(
            name_spot=random_lower_string(),
            camera_serial=equipment_create.serial_number,
            zone_id=zone.id,
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "number_spot": 1,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                }
            ],
        )
        spot_create = await spot_services.create_spot(db, spot_in=spot_in)

        assert spot_create
        assert spot_create.camera_id == equipment_create.id
        assert spot_create.zone_id == zone.id

    async def test_update_status_full_spot(self, db: AsyncSession):
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
            equipment_type=EquipmentType.SENSOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        number_spot = 1

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)

        spot_in = spotsSchemas.SpotCreate(
            name_spot=random_lower_string(),
            camera_serial=equipment_create.serial_number,
            zone_id=zone.id,
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "number_spot": number_spot,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                }
            ],
        )
        await spot_services.create_spot(db, spot_in=spot_in)

        check_spot = await crud.spot_repo.one_spot(
            db,
            input_camera_id=equipment_create.id,
            input_number_spot=number_spot,
        )
        update_status_spot_in = spotsSchemas.SpotUpdateStatus(
            camera_serial=equipment_create.serial_number,
            number_spot=number_spot,
            plate=random_lower_string(),
            lpr_image_id=image.id,
            plate_image_id=image.id,
            status=status_spot.full,
        )
        check_spot.plate = update_status_spot_in.plate
        check_spot.status = update_status_spot_in.status
        check_spot.lpr_image_id = update_status_spot_in.lpr_image_id
        check_spot.plate_image_id = update_status_spot_in.plate_image_id
        check_spot.latest_time_modified = datetime.now()

        spot_update = await crud.spot_repo.update(db, db_obj=check_spot)
        assert spot_update.status == update_status_spot_in.status

    async def test_update_status_entrancedoor_spot(self, db: AsyncSession):
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
            equipment_type=EquipmentType.SENSOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        number_spot = 1

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)

        spot_in = spotsSchemas.SpotCreate(
            name_spot=random_lower_string(),
            camera_serial=equipment_create.serial_number,
            zone_id=zone.id,
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "number_spot": number_spot,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                }
            ],
        )
        await spot_services.create_spot(db, spot_in=spot_in)

        check_spot = await crud.spot_repo.one_spot(
            db,
            input_camera_id=equipment_create.id,
            input_number_spot=number_spot,
        )
        update_status_spot_in = spotsSchemas.SpotUpdateStatus(
            camera_serial=equipment_create.serial_number,
            number_spot=number_spot,
            plate=random_lower_string(),
            lpr_image_id=image.id,
            plate_image_id=image.id,
            status=status_spot.entranceDoor,
        )
        check_spot.plate = update_status_spot_in.plate
        check_spot.status = update_status_spot_in.status
        check_spot.lpr_image_id = update_status_spot_in.lpr_image_id
        check_spot.plate_image_id = update_status_spot_in.plate_image_id
        check_spot.latest_time_modified = datetime.now()

        spot_update = await crud.spot_repo.update(db, db_obj=check_spot)
        assert spot_update.status == update_status_spot_in.status

    async def test_update_status_exitdoor_spot(self, db: AsyncSession):
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
            equipment_type=EquipmentType.SENSOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        number_spot = 1

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)

        spot_in = spotsSchemas.SpotCreate(
            name_spot=random_lower_string(),
            camera_serial=equipment_create.serial_number,
            zone_id=zone.id,
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "number_spot": number_spot,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                }
            ],
        )
        await spot_services.create_spot(db, spot_in=spot_in)

        check_spot = await crud.spot_repo.one_spot(
            db,
            input_camera_id=equipment_create.id,
            input_number_spot=number_spot,
        )
        update_status_spot_in = spotsSchemas.SpotUpdateStatus(
            camera_serial=equipment_create.serial_number,
            number_spot=number_spot,
            plate=random_lower_string(),
            lpr_image_id=image.id,
            plate_image_id=image.id,
            status=status_spot.exitDoor,
        )
        check_spot.plate = update_status_spot_in.plate
        check_spot.status = update_status_spot_in.status
        check_spot.lpr_image_id = update_status_spot_in.lpr_image_id
        check_spot.plate_image_id = update_status_spot_in.plate_image_id
        check_spot.latest_time_modified = datetime.now()

        spot_update = await crud.spot_repo.update(db, db_obj=check_spot)
        assert spot_update.status == update_status_spot_in.status

    async def test_update_status_empty_spot(self, db: AsyncSession):
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
            equipment_type=EquipmentType.SENSOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        number_spot = 1

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)

        spot_in = spotsSchemas.SpotCreate(
            name_spot=random_lower_string(),
            camera_serial=equipment_create.serial_number,
            zone_id=zone.id,
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "number_spot": number_spot,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                }
            ],
        )
        await spot_services.create_spot(db, spot_in=spot_in)

        check_spot = await crud.spot_repo.one_spot(
            db,
            input_camera_id=equipment_create.id,
            input_number_spot=number_spot,
        )
        update_status_spot_in = spotsSchemas.SpotUpdateStatus(
            camera_serial=equipment_create.serial_number,
            number_spot=number_spot,
            status=status_spot.empty,
        )
        check_spot.plate = None
        check_spot.status = update_status_spot_in.status
        check_spot.lpr_image_id = None
        check_spot.plate_image_id = None
        check_spot.latest_time_modified = datetime.now()

        spot_update = await crud.spot_repo.update(db, db_obj=check_spot)
        assert spot_update.status == update_status_spot_in.status

    async def test_get_multi_status(self, db: AsyncSession):
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
            equipment_type=EquipmentType.SENSOR,
            serial_number=random_lower_string(),
            ip_address=random_lower_string(),
            zone_id=zone.id,
            image_id=image.id,
        )

        number_spot = 1

        equipment_create = await equipment_repo.create(db, obj_in=equipment_in)

        spot_in = spotsSchemas.SpotCreate(
            name_spot=random_lower_string(),
            camera_serial=equipment_create.serial_number,
            zone_id=zone.id,
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.25, 0], [1, 1]],
                    "coordinates_rectangle_small": [[1, 1], [0, 0]],
                    "number_spot": number_spot,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                }
            ],
        )
        await spot_services.create_spot(db, spot_in=spot_in)

        check_spot = await crud.spot_repo.one_spot(
            db,
            input_camera_id=equipment_create.id,
            input_number_spot=number_spot,
        )
        update_status_spot_in = spotsSchemas.SpotUpdateStatus(
            camera_serial=equipment_create.serial_number,
            number_spot=number_spot,
            status=status_spot.empty,
        )
        check_spot.plate = None
        check_spot.status = update_status_spot_in.status
        check_spot.lpr_image_id = None
        check_spot.plate_image_id = None
        check_spot.latest_time_modified = datetime.now()

        spot_update = await crud.spot_repo.update(db, db_obj=check_spot)

        spots = await crud.spot_repo.get_multi_with_filters(
            db,
            input_camera_id=equipment_create.id,
            input_number_spot=number_spot,
            input_zone_id=zone.id,
        )

        for spot in spots:
            assert spot.status == spot_update.status
            assert spot.plate == spot_update.plate
