import random
import string
import time
from datetime import datetime, timedelta
import requests
from image_data_base64 import image, lpr_img1, lpr_img2, ocr_img1, ocr_img2
from app import schemas
from app.core.config import settings
from app.parking.schemas import camera as cameraShemas
from app.parking.schemas import parking as parkingSchemas
from app.parking.schemas import parkinglot as parkinglotShemas
from app.parking.schemas import parkingzone as zoneSchemas
from app.pricing.schemas import price as priceSchemas

url = settings.URL_FOR_SET_DATA_FAKE
headers = {"Content-Type": "application/json"}
auth = (settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD)


"""
--------------        gen random str           -----------------
"""


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for i in range(length))
    return random_string


def main_request(list: list):
    if "parking" in list:

        """
        --------------        create parking main            -----------------
        """
        data_create_parking = parkingSchemas.ParkingCreate(
            name="iranmal",
            brand_name="iranmal",
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
            beneficiary_data=parkingSchemas.Beneficiary(
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
        parking = requests.post(
            f"{url}/parking/main",
            data=data_create_parking.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("parking", parking.url, parking.status_code)
    else:
        parking = requests.get(
            f"{url}/parking/main", auth=auth, headers=headers
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
    if "zone" in list:
        zone1 = zoneSchemas.ParkingZoneCreate(
            name=f"z1c1-30{generate_random_string(3)}",
            tag=generate_random_string(5),
            parking_id=parking.json()["content"]["id"],
        )

        zone2 = zoneSchemas.ParkingZoneCreate(
            name=f"z2c1-90{generate_random_string(3)}",
            tag=generate_random_string(5),
            parking_id=parking.json()["content"]["id"],
        )

        zone1_create = requests.post(
            f"{url}/parkingzone/",
            data=zone1.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        sub1_zone1 = zoneSchemas.ParkingZoneCreate(
            name=f"sz1c1-15{generate_random_string(3)}",
            tag=generate_random_string(5),
            parking_id=parking.json()["content"]["id"],
            parent_id=zone1_create.json()["content"]["id"],
        )

        sub2_zone1 = zoneSchemas.ParkingZoneCreate(
            name=f"sz1c16-30{generate_random_string(3)}",
            tag=generate_random_string(5),
            parking_id=parking.json()["content"]["id"],
            parent_id=zone1_create.json()["content"]["id"],
        )
        print("zone 1", zone1_create.url, zone1_create.status_code)
        sub1_zone1_create = requests.post(
            f"{url}/parkingzone/",
            data=sub1_zone1.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print(
            "sub1 zone 1", sub1_zone1_create.url, sub1_zone1_create.status_code
        )
        sub2_zone1_create = requests.post(
            f"{url}/parkingzone/",
            data=sub2_zone1.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print(
            "sub2 zone 1", sub2_zone1_create.url, sub2_zone1_create.status_code
        )
        zone2_create = requests.post(
            f"{url}/parkingzone/",
            data=zone2.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("zone 2", zone2_create.url, zone2_create.status_code)
        sub1_zone2 = zoneSchemas.ParkingZoneCreate(
            name=f"sz1c1-30{generate_random_string(3)}",
            tag=generate_random_string(5),
            parking_id=parking.json()["content"]["id"],
            parent_id=zone2_create.json()["content"]["id"],
        )

        sub1_zone2_create = requests.post(
            f"{url}/parkingzone/",
            data=sub1_zone2.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        sub1_sub1_zone2 = zoneSchemas.ParkingZoneCreate(
            name=f"z1c30-90{generate_random_string(3)}",
            tag=generate_random_string(5),
            parking_id=parking.json()["content"]["id"],
            parent_id=sub1_zone2_create.json()["content"]["id"],
        )
        print(
            "sub 1 zone 2",
            sub1_zone2_create.url,
            sub1_zone2_create.status_code,
        )
        sub1_sub1_zone2_create = requests.post(
            f"{url}/parkingzone/",
            data=sub1_sub1_zone2.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print(
            "sub 1 sub 1 zone 1",
            sub1_sub1_zone2_create.url,
            sub1_sub1_zone2_create.status_code,
        )

    """
    --------------        create image            -----------------
    """
    if "image" in list:
        data_image = schemas.ImageCreateBase64(image=image)

        lpr1_img = schemas.ImageCreateBase64(image=lpr_img1)

        ocr1_img = schemas.ImageCreateBase64(image=ocr_img1)

        lpr2_img = schemas.ImageCreateBase64(image=lpr_img2)

        ocr2_img = schemas.ImageCreateBase64(image=ocr_img2)

        img_create = requests.post(
            f"{url}/images/", data=data_image.model_dump_json(), auth=auth
        )
        print("image main", img_create.url, img_create.status_code)
        lpr1_img_create = requests.post(
            f"{url}/images/",
            data=lpr1_img.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("image lpr1", lpr1_img_create.url, lpr1_img_create.status_code)
        ocr1_img_create = requests.post(
            f"{url}/images/",
            data=ocr1_img.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("image ocr1", ocr1_img_create.url, ocr1_img_create.status_code)
        lpr2_img_create = requests.post(
            f"{url}/images/",
            data=lpr2_img.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("image lpr2", lpr2_img_create.url, lpr2_img_create.status_code)
        ocr2_img_create = requests.post(
            f"{url}/images/",
            data=ocr2_img.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("image ocr2", ocr2_img_create.url, ocr2_img_create.status_code)

    """
    --------------        create camera            -----------------
    """
    if "camera" in list:
        data_camera_entrance_door = cameraShemas.CameraCreate(
            is_active=True,
            camera_ip="127.0.0.1",
            camera_code="entrance door",
            location="z1c",
            image_id=img_create.json()["content"]["id"],
        )
        data_camera_exit_door_create = cameraShemas.CameraCreate(
            is_active=True,
            camera_ip="127.0.0.1",
            camera_code="exit door",
            location="z1c",
            image_id=img_create.json()["content"]["id"],
        )

        camera_entrance_door_create = requests.post(
            f"{url}/camera/",
            data=data_camera_entrance_door.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print(
            "camera",
            camera_entrance_door_create.url,
            camera_entrance_door_create.status_code,
        )
        camera_exit_door_create = requests.post(
            f"{url}/camera/",
            data=data_camera_exit_door_create.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print(
            "camera",
            camera_exit_door_create.url,
            camera_exit_door_create.status_code,
        )
        camera_entrance_door_create = camera_entrance_door_create.json()[
            "content"
        ]["id"]
        camera_exit_door_create = camera_exit_door_create.json()["content"][
            "id"
        ]
    else:
        params = [
            {"input_camera_code": "entrance door"},
            {"input_camera_code": "exit door"},
        ]
        camera_entrance_door_create = requests.get(
            f"{url}/camera/search", params=params[0], auth=auth
        ).json()["content"]["items"][0]["id"]
        camera_exit_door_create = requests.get(
            f"{url}/camera/search", params=params[1], auth=auth
        ).json()["content"]["items"][0]["id"]

    """
    --------------        create pricing            -----------------
    """
    if "price" in list:
        data_price = priceSchemas.PriceCreate(
            price_model=priceSchemas.WeeklyDaysPriceModel(
                price_type="weekly",
                saturday=10,
                sunday=20,
                monday=30,
                tuesday=4,
                wednesday=50,
                thursday=60,
                friday=70,
            ),
            name=generate_random_string(5),
            name_fa="هفتگی",
            entrance_fee=1,
            hourly_fee=1,
            daily_fee=1,
            penalty_fee=1,
            expiration_datetime=str(datetime.now() + timedelta(days=365)),
            parking_id=parking.json()["content"]["id"],
            zone_ids=[
                zone1_create.json()["content"]["id"],
                sub1_zone1_create.json()["content"]["id"],
                sub2_zone1_create.json()["content"]["id"],
                zone2_create.json()["content"]["id"],
                sub1_zone2_create.json()["content"]["id"],
                sub1_sub1_zone2_create.json()["content"]["id"],
            ],
            priority=1,
        )
        data_price2 = priceSchemas.PriceCreate(
            price_model=priceSchemas.ZonePriceModel(
                price_type="zone", price=1000
            ),
            name=generate_random_string(5),
            name_fa="مکان",
            entrance_fee=1,
            hourly_fee=1,
            daily_fee=1,
            penalty_fee=1,
            expiration_datetime=str(datetime.now() + timedelta(days=365)),
            parking_id=parking.json()["content"]["id"],
            zone_ids=[
                zone1_create.json()["content"]["id"],
                sub1_zone1_create.json()["content"]["id"],
                sub2_zone1_create.json()["content"]["id"],
                zone2_create.json()["content"]["id"],
                sub1_zone2_create.json()["content"]["id"],
                sub1_sub1_zone2_create.json()["content"]["id"],
            ],
            priority=1,
        )

        price_create = requests.post(
            f"{url}/price/",
            data=data_price.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("create price1", price_create.url, price_create.status_code)
        price_create2 = requests.post(
            f"{url}/price/",
            data=data_price2.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("create price2", price_create2.url, price_create2.status_code)
        price_create = price_create.json()["content"]["id"]
        price_create2 = price_create2.json()["content"]["id"]

    else:
        params_price = [
            {"input_model_price": "هفتگی"},
            {"input_model_price": "مکان"},
        ]

        price_create = requests.get(
            f"{url}/price/search",
            params=params_price[0]["input_model_price"],
            auth=auth,
            headers=headers,
        ).json()["content"][0]["id"]

        price_create2 = requests.get(
            f"{url}/price/search",
            params=params_price[1]["input_model_price"],
            auth=auth,
            headers=headers,
        ).json()["content"][0]["id"]

    """
    --------------        create parling lot            -----------------
    """
    if "parkinglot" in list:
        data_lots = parkinglotShemas.ParkingLotCreate(
            floor_number=random.randint(1, 10),
            floor_name=generate_random_string(5),
            name_parkinglot=generate_random_string(5),
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.58, 0.26], [1.887, 1.3]],
                    "coordinates_rectangle_small": [[0.55, 0.20], [1.05, 1.0]],
                    "number_line": 1,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                    "price_model_id": price_create,
                }
            ],
            camera_id=camera_entrance_door_create,
            zone_id=sub1_zone1_create.json()["content"]["id"],
        )
        data_lots2 = parkinglotShemas.ParkingLotCreate(
            floor_number=random.randint(1, 10),
            floor_name=generate_random_string(5),
            name_parkinglot=generate_random_string(5),
            coordinates_rectangles=[
                {
                    "coordinates_rectangle_big": [[0.58, 0.26], [1.887, 1.3]],
                    "coordinates_rectangle_small": [[0.55, 0.20], [1.05, 1.0]],
                    "number_line": 1,
                    "percent_rotation_rectangle_big": 90,
                    "percent_rotation_rectangle_small": 90,
                    "price_model_id": price_create2,
                },
            ],
            camera_id=camera_exit_door_create,
            zone_id=sub1_zone1_create.json()["content"]["id"],
        )

        lot_create = requests.post(
            f"{url}/parkinglot/",
            data=data_lots.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("lot entrance", lot_create.url, lot_create.status_code)
        lot_create2 = requests.post(
            f"{url}/parkinglot/",
            data=data_lots2.model_dump_json(),
            auth=auth,
            headers=headers,
        )
        print("lot exit", lot_create2.url, lot_create2.status_code)
    else:

        lot_create = requests.get(
            f"{url}/parkinglot/entrance door",
            auth=auth,
            headers=headers,
        )

        lot_create2 = requests.get(
            f"{url}/parkinglot/exit door",
            auth=auth,
            headers=headers,
        )

        if not (
            (lot_create.json()["header"]["status"] == 0)
            and (lot_create2.json()["header"]["status"] == 0)
        ):
            raise Exception("please create lots")

    """
    --------------        create plate and record            -----------------
    """
    if "plate" in list:
        data_plate1 = schemas.PlateCreate(
            ocr="77ج44366",
            lpr_id=ocr1_img_create.json()["content"]["id"],
            big_image_id=lpr1_img_create.json()["content"]["id"],
            record_time="2024-07-15T09:20:37.480Z",
            camera_id=camera_entrance_door_create.json()["content"]["id"],
            number_line=1,  # importent create to lot
            floor_number=-1,  # importent create to lot
            floor_name="iranmal",  # importent create to lot
            name_parkinglot="lot1",  # importent create to lot
            price_model=price_create.json()["content"]["price_model"],
        )
        data_plate2 = schemas.PlateCreate(
            ocr="12ب34511",
            lpr_id=ocr2_img_create.json()["content"]["id"],
            big_image_id=lpr2_img_create.json()["content"]["id"],
            record_time="2024-07-15T09:20:37.480Z",
            camera_id=camera_exit_door_create.json()["content"]["id"],
            number_line=1,  # importent create to lot
            floor_number=-1,  # importent create to lot
            floor_name="iranmal",  # importent create to lot
            name_parkinglot="lot1",  # importent create to lot
            price_model=price_create.json()["content"]["price_model"],
        )

        i = 0
        while i < 5:
            plate_create1 = requests.post(
                f"{url}/plates/",
                data=data_plate1.model_dump_json(),
                auth=auth,
                headers=headers,
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
                f"{url}/plates/",
                data=data_plate2.model_dump_json(),
                auth=auth,
                headers=headers,
            )
            print(
                "plate2",
                plate_create2.url,
                plate_create2.status_code,
                plate_create2.json()["content"],
            )
            j += 1

    """
    -------------------     update status parking lot and create plate and record       ------------------------

    This data create plate and record necessity call plate endpoint

    """
    if "status" in list:
        data1_USPLots = parkinglotShemas.ParkingLotUpdateStatus(
            camera_code="entrance door",
            number_line=1,
            status="empty",
            latest_time_modified=datetime.now().isoformat(),
        )
        data2_USPLots = parkinglotShemas.ParkingLotUpdateStatus(
            camera_code="exit door",
            number_line=1,
            status="empty",
            latest_time_modified=datetime.now().isoformat(),
        )
        data3_USPLots = parkinglotShemas.ParkingLotUpdateStatus(
            camera_code="entrance door",
            number_line=1,
            ocr_img_id=ocr1_img_create.json()["content"]["id"],
            lpr_img_id=lpr1_img_create.json()["content"]["id"],
            ocr="77ج44366",
            status="entranceDoor",
            latest_time_modified=datetime.now().isoformat(),
        )
        data4_USPLots = parkinglotShemas.ParkingLotUpdateStatus(
            camera_code="exit door",
            number_line=1,
            ocr_img_id=ocr1_img_create.json()["content"]["id"],
            lpr_img_id=lpr1_img_create.json()["content"]["id"],
            ocr="77ج44366",
            status="exitDoor",
            latest_time_modified=datetime.now().isoformat(),
        )
        data5_USPLots = parkinglotShemas.ParkingLotUpdateStatus(
            camera_code="entrance door",
            number_line=1,
            ocr_img_id=ocr2_img_create.json()["content"]["id"],
            lpr_img_id=lpr2_img_create.json()["content"]["id"],
            ocr="12ب34511",
            status="entranceDoor",
            latest_time_modified=datetime.now().isoformat(),
        )
        data6_USPLots = parkinglotShemas.ParkingLotUpdateStatus(
            camera_code="exit door",
            number_line=1,
            ocr_img_id=ocr2_img_create.json()["content"]["id"],
            lpr_img_id=lpr2_img_create.json()["content"]["id"],
            ocr="12ب34511",
            status="exitDoor",
            latest_time_modified=datetime.now().isoformat(),
        )
        data_status = [
            data1_USPLots,
            data2_USPLots,
            data3_USPLots,
            data4_USPLots,
            data5_USPLots,
            data6_USPLots,
        ]

        s = 0
        while s < 20:

            data_status_lot = random.choice(data_status)
            print(data_status_lot)
            status_lot = requests.post(
                f"{url}/parkinglot/update_status/",
                data=data_status_lot.model_dump_json(),
                auth=auth,
                headers=headers,
            )
            print("status_lot", status_lot.url, status_lot.status_code)
            if status_lot.status_code == 400:
                print(status_lot.json())
            time.sleep(10)
            s += 1

    return


if __name__ == "__main__":
    req_name = [
        "parking",
        "zone",
        "image",
        # "camera",
        "price",
        "parkinglot",
        "status",
        # "plate",
    ]
    main_request(req_name)
