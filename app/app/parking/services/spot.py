from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas, utils
from app.parking.schemas import spot as spotsSchemas
from app.core import exceptions as exc
from app.core.celery_app import celery_app
from app.parking.repo import parkingzone_repo
from app.utils import PaginatedContent


async def create_line(
    db: AsyncSession, spot_in: schemas.SpotCreate
) -> schemas.SpotInDBBase:

    if spot_in.zone_id:
        zone = await parkingzone_repo.get(db, id=spot_in.zone_id)
        if not zone:
            raise exc.ServiceFailure(
                detail="Zone not found.",
                msg_code=utils.MessageCodes.not_found,
            )

    # check line number
    check_line_number = set()
    for i in spot_in.coordinates_rectangles:
        if i["number_line"] in check_line_number:
            raise exc.ServiceFailure(
                detail="for this camera,s number line confilict.",
                msg_code=utils.MessageCodes.operation_failed,
            )
        check_line_number.add(i["number_line"])

    # check camera exist
    camera = await crud.camera_repo.get(db, id=spot_in.camera_id)
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    # update line's camera
    find_spot = await crud.spot_repo.find_lines(
        db, input_camera_id=spot_in.camera_id
    )
    if find_spot:
        for p in find_spot:
            await crud.spot_repo._remove_async(db, id=p.id)

    # create new line's
    coordinates_rectangles = []
    for coordinate in spot_in.coordinates_rectangles:
        # This schemas change map field to save to db
        new_obj = schemas.SpotCreateLineInDB(
            camera_id=spot_in.camera_id,
            percent_rotation_rectangle_small=coordinate[
                "percent_rotation_rectangle_small"
            ],
            percent_rotation_rectangle_big=coordinate[
                "percent_rotation_rectangle_big"
            ],
            name_spot=spot_in.name_spot,
            number_line=coordinate["number_line"],
            coordinates_rectangle_big=coordinate["coordinates_rectangle_big"],
            coordinates_rectangle_small=coordinate[
                "coordinates_rectangle_small"
            ],
            price_model_id=coordinate["price_model_id"],
            zone_id=spot_in.zone_id,
        )
        items = await crud.spot_repo.create(db, obj_in=new_obj)
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
    return schemas.SpotInDBBase(
        camera_id=items.camera_id,
        name_spot=items.name_spot,
        coordinates_rectangles=coordinates_rectangles,
        # This id,created,modified lates record save in DB
        created=items.created,
        id=items.id,
        modified=items.modified,
    )


async def update_status(
    db: AsyncSession, spot_in: schemas.SpotUpdateStatus
) -> schemas.SpotUpdateStatus:
    camera = await crud.camera_repo.one_camera(
        db, input_camera_code=spot_in.camera_code
    )

    check = await crud.spot_repo.one_spot(
        db,
        input_camera_id=camera.id,
        input_number_line=spot_in.number_line,
    )
    if not check:
        raise exc.ServiceFailure(
            detail="line's camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )
    if (
        spot_in.status == spotsSchemas.Status.full.value
        or spotsSchemas.Status.entranceDoor.value
        or spotsSchemas.Status.exitDoor.value
    ):

        plate_in = schemas.PlateCreate(
            plate=spot_in.plate,
            record_time=datetime.now().isoformat(),
            lpr_image_id=(
                spot_in.lpr_image_id
                if spot_in.lpr_image_id
                else None
            ),
            plate_image_id=(
                spot_in.plate_image_id
                if spot_in.plate_image_id
                else None
            ),
            spot_id=check.id,
            zone_id=check.zone_id,
            camera_id=camera.id,
            price_model_id=check.price_model_id,
            type_status_spot=spot_in.status,
        )

        celery_app.send_task(
            "add_plates",
            args=[jsonable_encoder(plate_in)],
        )

    check.plate = spot_in.plate
    check.status = spot_in.status
    check.lpr_image_id = spot_in.lpr_image_id
    check.plate_image_id = spot_in.plate_image_id
    check.latest_time_modified = datetime.now()
    return await crud.spot_repo.update(db, db_obj=check)


async def get_status(
    db: AsyncSession,
    params: spotsSchemas.ParamsSpotStatus,
):
    spot_details = []
    spots = await crud.spot_repo.get_multi(db)
    for spot in spots:
        spot_details.append(
            {
                "id": spot.id,
                "camera_id": spot.camera_id,
                "name_spot": spot.name_spot,
                "zone_id": spot.zone_id,
                "coordinates_rectangles": [
                    {
                        "percent_rotation_rectangle_small": spot.percent_rotation_rectangle_small,
                        "percent_rotation_rectangle_big": spot.percent_rotation_rectangle_big,
                        "number_line": spot.number_line,
                        "coordinates_rectangle_big": spot.coordinates_rectangle_big,
                        "coordinates_rectangle_small": spot.coordinates_rectangle_small,
                        "price_model_id": spot.price_model_id,
                        "status": spot.status,
                        "plate": spot.plate,
                        "latest_time_modified": spot.latest_time_modified,
                        "lpr_image_id": spot.lpr_image_id,
                        "plate_image_id": spot.plate_image_id,
                    }
                ],
            }
        )
    if params.size is not None:  # limit
        spot_details = spot_details[: params.size]

    if params.page is not None:  # skip
        spot_details = spot_details[:: params.page]

    if params.asc:
        spot_details.reverse()

    return PaginatedContent(
        data=spot_details,
        total_count=len(spot_details),
        size=params.size,
        page=params.page,
    )


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
    spot_lines = await crud.spot_repo.find_lines(
        db, input_camera_id=camera.id
    )

    coordinate_details = []
    for line in spot_lines:
        coordinate_details.append(
            jsonable_encoder(
                spotsSchemas.CoordinateSpotsByCamera(
                    percent_rotation_rectangle_small=line.percent_rotation_rectangle_small,
                    percent_rotation_rectangle_big=line.percent_rotation_rectangle_big,
                    number_line=line.number_line,
                    status=line.status,
                    lpr_image_id=line.lpr_image_id,
                    plate_image_id=line.plate_image_id,
                    coordinates_rectangle_big=line.coordinates_rectangle_big,
                    coordinates_rectangle_small=line.coordinates_rectangle_small,
                    price_model_id=line.price_model_id,
                    zone_id=line.zone_id,
                    name_spot=line.name_spot,
                )
            )
        )
    return spotsSchemas.SpotsByCamera(
        camera_id=camera.id, coordinates_rectangles=coordinate_details
    )


async def get_details_spot_by_zone_id(db: AsyncSession, zone_id: int):

    spots = await crud.spot_repo.find_lines(db, input_zone_id=zone_id)

    all_spots_zone = []
    coordinate_details = []

    for line in spots:
        coordinate_details.append(
            {
                "percent_rotation_rectangle_small": line.percent_rotation_rectangle_small,
                "percent_rotation_rectangle_big": line.percent_rotation_rectangle_big,
                "number_line": line.number_line,
                "status": line.status,
                "lpr_image_id": line.lpr_image_id,
                "plate_image_id": line.plate_image_id,
                "coordinates_rectangle_big": line.coordinates_rectangle_big,
                "coordinates_rectangle_small": line.coordinates_rectangle_small,
                "price_model_id": line.price_model_id,
            }
        )

        list_spots = schemas.SpotCreate(
            camera_id=line.camera_id,
            name_spot=line.name_spot,
            zone_id=line.zone_id,
            coordinates_rectangles=coordinate_details,
        )
        all_spots_zone.append(list_spots)

    return all_spots_zone


async def update_price(
    db: AsyncSession, data: schemas.PriceUpdateInSpot
):

    find_park = await crud.spot_repo.get(db, id=data.id_park)
    find_park.price_model_id = data.price_model_id
    return await crud.spot_repo.update(db, db_obj=find_park)
