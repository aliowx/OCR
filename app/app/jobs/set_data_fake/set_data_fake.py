import requests
import random
import string
from app.core.config import settings
from app.parking.schemas import parking as pschemas
from app.parking.schemas import parkingzone as zschemas
from .image_data_base64 import lpr_img1, ocr_img1, lpr_img2, ocr_img2, image
from datetime import datetime, timedelta

url = "http://0.0.0.0:8585/park/api/v1"
headers = {"Content-Type": "application/json"}
auth = (settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD)


"""
--------------        gen random str           -----------------
"""


def generate_random_string(length, txt: None):
    "iranmal" if txt else None
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for i in range(length))
    return random_string


def main_request(list: list):
    """
    --------------        create parking main            -----------------
    """
    data_create_parking = pschemas.ParkingCreate(
        name=generate_random_string(5, True),
        brand_name=generate_random_string(5, True),
        floor_count=5,
        area=1,
        location_lat=-90,
        location_lon=-180,
        parking_address="teh",
        parking_logo_base64="logo",
        owner_first_name=generate_random_string(5),
        owner_last_name=generate_random_string(5),
        owner_national_id="ir-teh",
        owner_postal_code="iranmal",
        owner_phone_number="+98iranmal",
        owner_email="iranmal@gmail.com",
        owner_sheba_number="iranmal+123",
        owner_address="iranmal",
        owner_type=1,
        beneficiary_data=pschemas.Beneficiary(
            company_name="iranmal",
            company_register_code=generate_random_string(5),
            company_national_code=generate_random_string(5),
            company_economic_code=generate_random_string(5),
            company_email="iranmal@mail.com",
            company_phone_number=generate_random_string(5),
            company_postal_code=generate_random_string(5),
            company_sheba_number=generate_random_string(5),
            company_address=generate_random_string(5),
            beneficiary_type=1,
        ),
    )
    if "parking" in list:
        parking = requests.post(
            f"{url}/parking/main", json=data_create_parking, auth=auth
        )
        print("parking", parking.url, parking.status_code)

    """
    --------------        create zone            -----------------
    """

    """
    example

    -zone 1
        -sub_zone1
        -sub_zone2

    -zone 2
        -sub_zone1
            -subzone1
    """

    zone1 = zschemas.ParkingZoneCreate(
        tag=generate_random_string(5),
        name="z1c1-30",
        parking_id=parking.json()["content"]["id"],
    )

    zone2 = {
        "tag": generate_random_string(5),
        "name": "z2c1-90",
        "parking_id": parking.json()["content"]["id"],
    }

    if "zone" in list:
        zone1_create = requests.post(
            f"{url}/parkingzone/", json=zone1, auth=auth
        )
        sub1_zone1 = zschemas.ParkingZoneCreate(
            tag=generate_random_string(5),
            name="sz1c1-15",
            parking_id=parking.json()["content"]["id"],
            parent_id=zone1_create.json()["content"]["id"],
        )

        sub2_zone1 = zschemas.ParkingZoneCreate(
            tag=generate_random_string(5),
            name="sz1c16-30",
            parking_id=parking.json()["content"]["id"],
            parent_id=zone1_create.json()["content"]["id"],
        )
        print("zone 1", zone1_create.url, zone1_create.status_code)
        sub1_zone1_create = requests.post(
            f"{url}/parkingzone/", json=sub1_zone1, auth=auth
        )
        print(
            "sub1 zone 1", sub1_zone1_create.url, sub1_zone1_create.status_code
        )
        sub2_zone1_create = requests.post(
            f"{url}/parkingzone/", json=sub2_zone1, auth=auth
        )
        print(
            "sub2 zone 1", sub2_zone1_create.url, sub2_zone1_create.status_code
        )
        zone2_create = requests.post(
            f"{url}/parkingzone/", json=zone2, auth=auth
        )
        print("zone 2", zone2_create.url, zone2_create.status_code)
        sub1_zone2 = zschemas.ParkingZoneCreate(
            tag=generate_random_string(5),
            name="sz1c1-30",
            parking_id=parking.json()["content"]["id"],
            parent_id=zone2_create.json()["content"]["id"],
        )

        sub1_sub1_zone2 = zschemas.ParkingZoneCreate(
            tag=generate_random_string(5),
            name="z1c30-90",
            parking_id=parking.json()["content"]["id"],
            parent_id=sub1_zone2_create.json()["content"]["id"],
        )
        sub1_zone2_create = requests.post(
            f"{url}/parkingzone/", json=sub1_zone2, auth=auth
        )
        print(
            "sub 1 zone 2",
            sub1_zone2_create.url,
            sub1_zone2_create.status_code,
        )
        sub1_sub1_zone2_create = requests.post(
            f"{url}/parkingzone/", json=sub1_sub1_zone2, auth=auth
        )
        print(
            "sub 1 sub 1 zone 1",
            sub1_sub1_zone2_create.url,
            sub1_sub1_zone2_create.status_code,
        )

    """
    --------------        create image            -----------------
    """

    data_image = {"image": image}

    lpr1_img = {"image": lpr_img1}

    ocr1_img = {"image": ocr_img1}

    lpr2_img = {"image": lpr_img2}

    ocr2_img = {"image": ocr_img2}

    if "image" in list:
        img_create = requests.post(
            f"{url}/images/", json=data_image, auth=auth
        )
        print("image main", img_create.url, img_create.status_code)
        lpr1_img_create = requests.post(
            f"{url}/images/", json=lpr1_img, auth=auth
        )
        print("image lpr1", lpr1_img_create.url, lpr1_img_create.status_code)
        ocr1_img_create = requests.post(
            f"{url}/images/", json=ocr1_img, auth=auth
        )
        print("image ocr1", ocr1_img_create.url, ocr1_img_create.status_code)
        lpr2_img_create = requests.post(
            f"{url}/images/", json=lpr2_img, auth=auth
        )
        print("image lpr2", lpr2_img_create.url, lpr2_img_create.status_code)
        ocr2_img_create = requests.post(
            f"{url}/images/", json=ocr2_img, auth=auth
        )
        print("image ocr2", ocr2_img_create.url, ocr2_img_create.status_code)

    """
    --------------        create camera            -----------------
    """

    data_camera = {
        "is_active": True,
        "camera_ip": "127.0.0.1",
        "camera_code": generate_random_string(5),
        "location": "z1c",
        "image_id": img_create.json()["content"]["id"],
    }
    if "camera" in list:
        camera_create = requests.post(
            f"{url}/camera/", json=data_camera, auth=auth
        )
        print("camera", camera_create.url, camera_create.status_code)

    """
    --------------        create pricing            -----------------
    """

    data_price = {
        "price_model": {
            "price_type": "weekly",
            "saturday": 10,
            "sunday": 20,
            "monday": 30,
            "tuesday": 4,
            "wednesday": 50,
            "thursday": 60,
            "friday": 70,
        },
        "name": generate_random_string(5),
        "name_fa": "هفتگی",
        "entrance_fee": 1,
        "hourly_fee": 1,
        "daily_fee": 1,
        "penalty_fee": 1,
        "expiration_datetime": str(datetime.now() + timedelta(days=365)),
        "parking_id": parking.json()["content"]["id"],
        "zone_ids": [
            zone1_create.json()["content"]["id"],
            sub1_zone1_create.json()["content"]["id"],
            sub2_zone1_create.json()["content"]["id"],
            zone2_create.json()["content"]["id"],
            sub1_zone2_create.json()["content"]["id"],
            sub1_sub1_zone2_create.json()["content"]["id"],
        ],
        "priority": 1,
    }
    data_price2 = {
        "price_model": {"price_type": "zone", "price": 1000},
        "name": generate_random_string(5),
        "name_fa": "مکان",
        "entrance_fee": 1,
        "hourly_fee": 1,
        "daily_fee": 1,
        "penalty_fee": 1,
        "expiration_datetime": str(datetime.now() + timedelta(days=365)),
        "parking_id": parking.json()["content"]["id"],
        "zone_ids": [
            zone1_create.json()["content"]["id"],
            sub1_zone1_create.json()["content"]["id"],
            sub2_zone1_create.json()["content"]["id"],
            zone2_create.json()["content"]["id"],
            sub1_zone2_create.json()["content"]["id"],
            sub1_sub1_zone2_create.json()["content"]["id"],
        ],
        "priority": 1,
    }
    if "price" in list:
        price_create = requests.post(
            f"{url}/price/", json=data_price, auth=auth
        )
        print("create price1", price_create.url, price_create.status_code)
        price_create2 = requests.post(
            f"{url}/price/", json=data_price2, auth=auth
        )
        print("create price2", price_create2.url, price_create2.status_code)

    """
    --------------        create parling lot            -----------------
    """

    data_lots = {
        "floor_number": random.randint(1, 10),
        "floor_name": generate_random_string(5),
        "name_parkinglot": generate_random_string(5),
        "coordinates_rectangles": [
            {
                "coordinates_rectangle_big": [[0.58, 0.26], [1.887, 1.3]],
                "coordinates_rectangle_small": [[0.55, 0.20], [1.05, 1.0]],
                "number_line": 1,
                "percent_rotation_rectangle_big": 90,
                "percent_rotation_rectangle_small": 90,
                "price_model_id": price_create.json()["content"]["id"],
            },
            {
                "coordinates_rectangle_big": [[0.58, 0.26], [1.887, 1.3]],
                "coordinates_rectangle_small": [[0.55, 0.20], [1.05, 1.0]],
                "number_line": 1,
                "percent_rotation_rectangle_big": 90,
                "percent_rotation_rectangle_small": 90,
                "price_model_id": price_create2.json()["content"]["id"],
            },
        ],
        "camera_id": camera_create.json()["content"]["id"],
        "zone_id": sub1_zone1_create.json()["content"]["id"],
    }
    if "parkinglot" in list:
        lot_create = requests.post(
            f"{url}/parkinglot/", json=data_lots, auth=auth, headers=headers
        )
        print("lot", lot_create.url, lot_create.status_code)

    """
    --------------        create plate and record            -----------------
    """

    data_plate1 = {
        "ocr": "77ج44366",
        "lpr_id": ocr1_img_create.json()["content"]["id"],
        "big_image_id": lpr1_img_create.json()["content"]["id"],
        "record_time": "2024-07-15T09:20:37.480Z",
        "camera_id": camera_create.json()["content"]["id"],
        "number_line": 1,  # importent create to lot
        "floor_number": -1,  # importent create to lot
        "floor_name": "iranmal",  # importent create to lot
        "name_parkinglot": "lot1",  # importent create to lot
        "price_model": price_create.json()["content"]["price_model"],
    }
    data_plate2 = {
        "ocr": "12ب34511",
        "lpr_id": ocr2_img_create.json()["content"]["id"],
        "big_image_id": lpr2_img_create.json()["content"]["id"],
        "record_time": "2024-07-15T09:20:37.480Z",
        "camera_id": camera_create.json()["content"]["id"],
        "number_line": 1,  # importent create to lot
        "floor_number": -1,  # importent create to lot
        "floor_name": "iranmal",  # importent create to lot
        "name_parkinglot": "lot1",  # importent create to lot
        "price_model": price_create.json()["content"]["price_model"],
    }
    if "plate" in list:
        i = 0
        while i < 5:
            plate_create1 = requests.post(
                f"{url}/plates/", json=data_plate1, auth=auth, headers=headers
            )
            print(
                "plate1",
                plate_create1.url,
                plate_create1.status_code,
                plate_create1.json()["content"],
            )
            i += 1

        j = 0
        while j < 7:
            plate_create2 = requests.post(
                f"{url}/plates/", json=data_plate2, auth=auth, headers=headers
            )
            print(
                "plate2",
                plate_create2.url,
                plate_create2.status_code,
                plate_create2.json()["content"],
            )
            j += 1


if __name__ == "__main__":
    req_name = [
        "parking",
        "zone",
        "image",
        "camera",
        "price",
        "parkinglot",
        "plate",
    ]
    main_request(req_name)
