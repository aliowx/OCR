from app import crud, models, schemas, utils
from app import exceptions as exc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from app.core.celery_app import celery_app


async def create_line(
    db: AsyncSession, parking_in: schemas.ParkingCreate
) -> schemas.ParkingInDBBase:

    # check line number
    check_line_number = set()
    for i in parking_in.coordinates_rectangles:
        if i["number_line"] in check_line_number:
            raise exc.ServiceFailure(
                detail="for this camera,s number line confilict.",
                msg_code=utils.MessageCodes.operation_failed,
            )
        check_line_number.add(i["number_line"])

    # check camera exist
    camera = await crud.camera.get(db, id=parking_in.camera_id)
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    # update line's camera
    find_parking = await crud.parking.find_lines_camera(
        db, input_camera_id=parking_in.camera_id
    )
    if find_parking:
        for p in find_parking:
            await crud.parking._remove_async(db, id=p.id)

    # create new line's
    coordinates_rectangles = []
    for coordinate in parking_in.coordinates_rectangles:
        # This schemas change map field to save to db
        new_obj = schemas.ParkingCreateLineInDB(
            camera_id=parking_in.camera_id,
            percent_rotation_rectangle_small=coordinate[
                "percent_rotation_rectangle_small"
            ],
            percent_rotation_rectangle_big=coordinate[
                "percent_rotation_rectangle_big"
            ],
            floor_name=parking_in.floor_name,
            floor_number=parking_in.floor_number,
            name_parking=parking_in.name_parking,
            number_line=coordinate["number_line"],
            coordinates_rectangle_big=coordinate["coordinates_rectangle_big"],
            coordinates_rectangle_small=coordinate[
                "coordinates_rectangle_small"
            ],
            price_model_id=coordinate["price_model_id"],
        )
        items = await crud.parking.create(db, obj_in=new_obj)
        if items:
            reverse_coordinates_rectangles = {
                "number_line": new_obj.number_line,
                "coordinates_rectangle_big": new_obj.coordinates_rectangle_big,
                "coordinates_rectangle_small": new_obj.coordinates_rectangle_small,
                "percent_rotation_rectangle_small": new_obj.percent_rotation_rectangle_small,
                "percent_rotation_rectangle_big": new_obj.percent_rotation_rectangle_big,
                "price_model_id": new_obj.price_model_id,
            }
            coordinates_rectangles.append(reverse_coordinates_rectangles)
    return schemas.ParkingInDBBase(
        camera_id=items.camera_id,
        floor_number=items.floor_number,
        floor_name=items.floor_name,
        name_parking=items.name_parking,
        coordinates_rectangles=coordinates_rectangles,
        # This id,created,modified lates record save in DB
        created=items.created,
        id=items.id,
        modified=items.modified,
    )


async def update_status(
    db: AsyncSession, parking_in: schemas.ParkingUpdateStatus
) -> schemas.ParkingUpdateStatus:
    camera = await crud.camera.one_camera(
        db, input_camera_code=parking_in.camera_code
    )

    check = await crud.parking.one_parking(
        db,
        input_camera_id=camera.id,
        input_number_line=parking_in.number_line,
    )
    if not check:
        raise exc.ServiceFailure(
            detail="line's camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    if parking_in.status == "full":
        plate_in = schemas.PlateCreate(
            ocr=parking_in.ocr,
            record_time=datetime.now().isoformat(),
            lpr_id=parking_in.ocr_img_id if parking_in.ocr_img_id else None,
            big_image_id=(
                parking_in.lpr_img_id if parking_in.lpr_img_id else None
            ),
            camera_id=camera.id,
            number_line=parking_in.number_line,
            floor_number=check.floor_number,
            floor_name=check.floor_name,
            name_parking=check.name_parking,
        )

        celery_app.send_task(
            "add_plates",
            args=[jsonable_encoder(plate_in)],
        )

    check.ocr = parking_in.ocr
    check.status = parking_in.status
    check.lpr_img_id = parking_in.lpr_img_id
    check.ocr_img_id = parking_in.ocr_img_id
    check.latest_time_modified = datetime.now()
    return await crud.parking.update(db, db_obj=check)


async def get_status(db: AsyncSession):
    parking_details = []
    parkings = await crud.parking.get_multi(db)

    for parking in parkings:
        parking_details.append(
            {
                "id": parking.id,
                "camera_id": parking.camera_id,
                "floor_number": parking.floor_number,
                "name_parking": parking.name_parking,
                "floor_name": parking.floor_name,
                "coordinates_rectangles": [
                    {
                        "percent_rotation_rectangle_small": parking.percent_rotation_rectangle_small,
                        "percent_rotation_rectangle_big": parking.percent_rotation_rectangle_big,
                        "number_line": parking.number_line,
                        "coordinates_rectangle_big": parking.coordinates_rectangle_big,
                        "coordinates_rectangle_small": parking.coordinates_rectangle_small,
                        "price_model_id": parking.price_model_id,
                        "status": parking.status,
                        "ocr": parking.ocr,
                        "latest_time_modified": parking.latest_time_modified,
                        "lpr_img": parking.lpr_img_id,
                        "ocr_img": parking.ocr_img_id,
                    }
                ],
            }
        )

    return parking_details


async def get_details_line_by_camera(db: AsyncSession, camera_code: str):
    camera = await crud.camera.one_camera(db, input_camera_code=camera_code)
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    # find line's camera
    parking_lines = await crud.parking.find_lines_camera(
        db, input_camera_id=camera.id
    )

    coordinate_details = []
    for line in parking_lines:
        coordinate_details.append(
            {
                "percent_rotation_rectangle_small": line.percent_rotation_rectangle_small,
                "percent_rotation_rectangle_big": line.percent_rotation_rectangle_big,
                "number_line": line.number_line,
                "status": line.status,
                "lpr_img_id": line.lpr_img_id,
                "ocr_img_id": line.ocr_img_id,
                "coordinates_rectangle_big": line.coordinates_rectangle_big,
                "coordinates_rectangle_small": line.coordinates_rectangle_small,
                "price_model_id": line.price_model_id,
            }
        )

    return schemas.ParkingCreate(
        camera_id=camera.id,
        floor_number=parking_lines[0].floor_number,
        floor_name=parking_lines[0].floor_name,
        name_parking=parking_lines[0].name_parking,
        coordinates_rectangles=coordinate_details,
    )


async def update_price(db: AsyncSession, data: schemas.PriceUpdateInParking):

    find_park = await crud.parking.get(db, id=data.id_park)
    find_park.price_model_id = data.price_model_id
    return await crud.parking.update(db, db_obj=find_park)
