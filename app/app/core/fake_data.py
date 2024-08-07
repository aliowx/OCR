from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict
from app.parking import schemas as ParkingSchema
from app import schemas as MainSchema
from app import models
from datetime import datetime, timedelta
import random
import string


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for i in range(length))
    return random_string


class FakeData(BaseSettings):

    PARKING: ClassVar = models.Parking(
        name="بازار بزرگ تهران",
        brand_name="ایران مال",
        floor_count=5,
        area=500,
        location_lat=35.7537155,
        location_lon=51.1923977,
        parking_address="تهران، اتوبان شهید همت (غرب)، اتوبان شهید خرازی ",
        parking_logo_image_id=None,
        owner_first_name="مالک 1",
        owner_last_name="مالکی",
        owner_national_id="2282512324",
        owner_postal_code="64654654",
        owner_phone_number="09216987654",
        owner_email="test@test.com",
        owner_sheba_number="984659874654",
        owner_address="test@test.com",
        owner_type=ParkingSchema.UserType.REAL,
        payment_type=ParkingSchema.ParkingPaymentType.AFTER_EXIT,
        beneficiary_data=ParkingSchema.Beneficiary(
            company_name="irantest",
            company_register_code="98453198",
            company_national_code="123456",
            company_economic_code="68465987",
            company_email="test@test.com",
            company_phone_number="12345",
            company_postal_code="12345",
            company_sheba_number="12345",
            company_address="test@test.com",
            beneficiary_type=ParkingSchema.UserType.REAL,
        ).model_dump(),
    )

    EQUIPMENT: ClassVar = models.Equipment(
        equipment_type=ParkingSchema.equipment.EquipmentType.CAMERA_ZONE,
        equipment_status=ParkingSchema.equipment.EquipmentStatus.HEALTHY,
        serial_number="abc123",
        ip_address="127.0.0.1",
        zone_id=1,
    )

    IMAGE: ClassVar = models.Image()

    ZONE: ClassVar = models.Zone(
        name="zone",
        tag="z-p",
        floor_name="one",
        floor_number=1,
        capacity=10,
        parent_id=None,
    )
    SUB_ZONE: ClassVar = models.Zone(
        name="sub_zone",
        tag="sz-c",
        floor_name="one",
        floor_number=1,
        capacity=5,
        parent_id=None,
    )

    RECORD1: ClassVar = models.Record(
        plate="plate1",
        start_time=datetime.now().isoformat(),
        end_time=datetime.now() + timedelta(hours=random.randint(1, 10)),
        best_lpr_image_id=None,
        best_plate_image_id=None,
        score=0.01,
        zone_id=None,
        latest_status=MainSchema.StatusRecord.finished.value,
    )

    PLATE1: ClassVar = models.Plate(
        plate="plate1" + generate_random_string(3),
        record_time=datetime.now(),
        plate_image_id=None,
        lpr_image_id=None,
        camera_id=None,
        zone_id=None,
        type_camera=MainSchema.plate.TypeCamera.entranceDoor,
        created=random.choice([datetime.now() - timedelta(days=i) for i in range(1,8)]),
    )

    RECORD2: ClassVar = models.Record(
        plate="plate2" + generate_random_string(3),
        start_time=datetime.now().isoformat(),
        end_time=datetime.now() + timedelta(hours=random.randint(1, 10)),
        best_lpr_image_id=None,
        best_plate_image_id=None,
        score=0.01,
        zone_id=None,
        latest_status=MainSchema.StatusRecord.finished.value,
        created=random.choice([datetime.now() - timedelta(days=i) for i in range(1,8)])
    )

    PLATE2: ClassVar = models.Plate(
        plate="plate2" + generate_random_string(3),
        record_time=datetime.now(),
        plate_image_id=None,
        lpr_image_id=None,
        camera_id=None,
        zone_id=None,
        type_camera=MainSchema.plate.TypeCamera.entranceDoor,
        created=random.choice([datetime.now() - timedelta(days=i) for i in range(0,8)])

    )

    RECORD_PAST: ClassVar = models.Record(
        plate="plate-ago-time" + generate_random_string(3),
        start_time=datetime.now().isoformat(),
        end_time=datetime.now() + timedelta(hours=random.randint(1, 10)),
        best_lpr_image_id=None,
        best_plate_image_id=None,
        score=0.01,
        zone_id=None,
        latest_status=MainSchema.StatusRecord.finished.value,
        created=datetime(
            year=random.randint(2023, 2025),
            month=random.randint(1, 12),
            day=random.randint(1, 30),
        ).isoformat(),
    )


fake_data = FakeData()
