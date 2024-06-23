from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas, utils
from app.parking.schemas import parkinglot as parkinglotsSchemas
from app.core import exceptions as exc
from app.core.celery_app import celery_app
from app.parking.repo import parkingzone_repo


async def create_line(
    db: AsyncSession, parkinglot_in: schemas.ParkingLotCreate
) -> schemas.ParkingLotInDBBase:

    if parkinglot_in.zone_id:
        zone = await parkingzone_repo.get(db, id=parkinglot_in.zone_id)
        if not zone:
            raise exc.ServiceFailure(
                detail="Zone not found.",
                msg_code=utils.MessageCodes.not_found,
            )

    # check line number
    check_line_number = set()
    for i in parkinglot_in.coordinates_rectangles:
        if i["number_line"] in check_line_number:
            raise exc.ServiceFailure(
                detail="for this camera,s number line confilict.",
                msg_code=utils.MessageCodes.operation_failed,
            )
        check_line_number.add(i["number_line"])

    # check camera exist
    camera = await crud.camera_repo.get(db, id=parkinglot_in.camera_id)
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    # update line's camera
    find_parkinglot = await crud.parkinglot_repo.find_lines(
        db, input_camera_id=parkinglot_in.camera_id
    )
    if find_parkinglot:
        for p in find_parkinglot:
            await crud.parkinglot_repo._remove_async(db, id=p.id)

    # create new line's
    coordinates_rectangles = []
    for coordinate in parkinglot_in.coordinates_rectangles:
        # This schemas change map field to save to db
        new_obj = schemas.ParkingLotCreateLineInDB(
            camera_id=parkinglot_in.camera_id,
            percent_rotation_rectangle_small=coordinate[
                "percent_rotation_rectangle_small"
            ],
            percent_rotation_rectangle_big=coordinate[
                "percent_rotation_rectangle_big"
            ],
            floor_name=parkinglot_in.floor_name,
            floor_number=parkinglot_in.floor_number,
            name_parkinglot=parkinglot_in.name_parkinglot,
            number_line=coordinate["number_line"],
            coordinates_rectangle_big=coordinate["coordinates_rectangle_big"],
            coordinates_rectangle_small=coordinate[
                "coordinates_rectangle_small"
            ],
            price_model_id=coordinate["price_model_id"],
            zone_id=parkinglot_in.zone_id
        )
        items = await crud.parkinglot_repo.create(db, obj_in=new_obj)
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
    return schemas.ParkingLotInDBBase(
        camera_id=items.camera_id,
        floor_number=items.floor_number,
        floor_name=items.floor_name,
        name_parkinglot=items.name_parkinglot,
        coordinates_rectangles=coordinates_rectangles,
        # This id,created,modified lates record save in DB
        created=items.created,
        id=items.id,
        modified=items.modified,
    )


async def update_status(
    db: AsyncSession, parkinglot_in: schemas.ParkingLotUpdateStatus
) -> schemas.ParkingLotUpdateStatus:
    camera = await crud.camera_repo.one_camera(
        db, input_camera_code=parkinglot_in.camera_code
    )

    check = await crud.parkinglot_repo.one_parkinglot(
        db,
        input_camera_id=camera.id,
        input_number_line=parkinglot_in.number_line,
    )
    if not check:
        raise exc.ServiceFailure(
            detail="line's camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )
    price_model = await crud.price_repo.get(db, id=check.price_model_id)
    if (
        parkinglot_in.status == parkinglotsSchemas.Status.full
        or parkinglotsSchemas.Status.entranceDoor
        or parkinglotsSchemas.Status.exitDoor
    ):
        plate_in = schemas.PlateCreate(
            ocr=parkinglot_in.ocr,
            record_time=datetime.now().isoformat(),
            lpr_id=(
                parkinglot_in.ocr_img_id if parkinglot_in.ocr_img_id else None
            ),
            big_image_id=(
                parkinglot_in.lpr_img_id if parkinglot_in.lpr_img_id else None
            ),
            camera_id=camera.id,
            number_line=parkinglot_in.number_line,
            floor_number=check.floor_number,
            floor_name=check.floor_name,
            name_parkinglot=check.name_parkinglot,
            price_model=price_model.price_model,
        )

        celery_app.send_task(
            "add_plates",
            args=[jsonable_encoder(plate_in)],
        )

    check.ocr = parkinglot_in.ocr
    check.status = parkinglot_in.status
    check.lpr_img_id = parkinglot_in.lpr_img_id
    check.ocr_img_id = parkinglot_in.ocr_img_id
    check.latest_time_modified = datetime.now()
    return await crud.parkinglot_repo.update(db, db_obj=check)


async def get_status(db: AsyncSession):
    parkinglot_details = []
    parkinglots = await crud.parkinglot_repo.get_multi(db)

    for parkinglot in parkinglots:
        parkinglot_details.append(
            {
                "id": parkinglot.id,
                "camera_id": parkinglot.camera_id,
                "floor_number": parkinglot.floor_number,
                "name_parkinglot": parkinglot.name_parkinglot,
                "floor_name": parkinglot.floor_name,
                "coordinates_rectangles": [
                    {
                        "percent_rotation_rectangle_small": parkinglot.percent_rotation_rectangle_small,
                        "percent_rotation_rectangle_big": parkinglot.percent_rotation_rectangle_big,
                        "number_line": parkinglot.number_line,
                        "coordinates_rectangle_big": parkinglot.coordinates_rectangle_big,
                        "coordinates_rectangle_small": parkinglot.coordinates_rectangle_small,
                        "price_model_id": parkinglot.price_model_id,
                        "status": parkinglot.status,
                        "ocr": parkinglot.ocr,
                        "latest_time_modified": parkinglot.latest_time_modified,
                        "lpr_img": parkinglot.lpr_img_id,
                        "ocr_img": parkinglot.ocr_img_id,
                    }
                ],
            }
        )

    return parkinglot_details


async def get_details_line_by_camera(db: AsyncSession, camera_code: str):
    camera = await crud.camera_repo.one_camera(
        db, input_camera_code=camera_code
    )
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    # find line's camera
    parkinglot_lines = await crud.parkinglot_repo.find_lines(
        db, input_camera_id=camera.id
    )

    coordinate_details = []
    for line in parkinglot_lines:
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
    # TODO return zone_id
    return schemas.ParkingLotCreate(
        camera_id=camera.id,
        floor_number=parkinglot_lines[0].floor_number,
        floor_name=parkinglot_lines[0].floor_name,
        name_parkinglot=parkinglot_lines[0].name_parkinglot,
        coordinates_rectangles=coordinate_details,
    )


async def get_details_lot_by_zone_id(db: AsyncSession, zone_id: int):

    lots = await crud.parkinglot_repo.find_lines(db, input_zone_id=zone_id)

    all_lots_zone = []
    coordinate_details = []

    for line in lots:
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

        list_lots = schemas.ParkingLotCreate(
            camera_id=line.camera_id,
            floor_number=line.floor_number,
            floor_name=line.floor_name,
            name_parkinglot=line.name_parkinglot,
            zone_id=line.zone_id,
            coordinates_rectangles=coordinate_details,
        )
        all_lots_zone.append(list_lots)

    return all_lots_zone


async def update_price(
    db: AsyncSession, data: schemas.PriceUpdateInParkingLot
):

    find_park = await crud.parkinglot_repo.get(db, id=data.id_park)
    find_park.price_model_id = data.price_model_id
    return await crud.parkinglot_repo.update(db, db_obj=find_park)
