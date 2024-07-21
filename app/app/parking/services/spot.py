from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas, utils
from app.parking.schemas import spot as spotsSchemas
from app.parking.schemas import SpotInfo, SpotInfoCoordinate
from app.core import exceptions as exc
from app.core.celery_app import celery_app
from app.parking.repo import zone_repo
from app.utils import PaginatedContent
from app.models.base import EquipmentType
from app.pricing.repo import price_repo
from app.pricing.services import get_main_price


async def create_spot(
    db: AsyncSession, spot_in: schemas.SpotCreate
) -> schemas.SpotInDBBase:

    if spot_in.zone_id:
        zone = await zone_repo.get(db, id=spot_in.zone_id)
        if not zone:
            raise exc.ServiceFailure(
                detail="Zone not found.",
                msg_code=utils.MessageCodes.not_found,
            )

    # check line number
    check_line_number = set()
    for i in spot_in.coordinates_rectangles:
        if i["number_spot"] in check_line_number:
            raise exc.ServiceFailure(
                detail="for this camera,s number spot confilict.",
                msg_code=utils.MessageCodes.operation_failed,
            )
        check_line_number.add(i["number_spot"])

    # check camera exist
    camera = await crud.equipment_repo.one_equipment(
        db, serial_number=spot_in.camera_serial
    )
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )
    
    if camera.equipment_type != EquipmentType.CAMERA_SPOT:
        raise exc.ServiceFailure(
            detail="type camera not spot",
            msg_code=utils.MessageCodes.operation_failed,
        )
    # TODO find number line after delete
    # update line's camera first step remove spot
    find_spot = await crud.spot_repo.get_multi_with_filters(
        db, input_camera_id=camera.id
    )
    if find_spot:
        for spot in find_spot:
            await crud.spot_repo._remove_async(db, id=spot.id)

    # create new line's
    coordinates_rectangles = []
    for coordinate in spot_in.coordinates_rectangles:
        # This schemas change map field to save to db
        new_spot = schemas.SpotCreateLineInDB(
            camera_id=camera.id,
            percent_rotation_rectangle_small=coordinate[
                "percent_rotation_rectangle_small"
            ],
            percent_rotation_rectangle_big=coordinate[
                "percent_rotation_rectangle_big"
            ],
            name_spot=spot_in.name_spot,
            number_spot=coordinate["number_spot"],
            coordinates_rectangle_big=coordinate["coordinates_rectangle_big"],
            coordinates_rectangle_small=coordinate[
                "coordinates_rectangle_small"
            ],
            zone_id=spot_in.zone_id,
        )
        items = await crud.spot_repo.create(db, obj_in=new_spot)
        if items:
            reverse_coordinates_rectangles = schemas.ReverseCoordinatesRectangles(
                number_spot=new_spot.number_spot,
                coordinates_rectangle_big=new_spot.coordinates_rectangle_big,
                coordinates_rectangle_small=new_spot.coordinates_rectangle_small,
                percent_rotation_rectangle_small=new_spot.percent_rotation_rectangle_small,
                percent_rotation_rectangle_big=new_spot.percent_rotation_rectangle_big,
            )
            coordinates_rectangles.append(
                jsonable_encoder(reverse_coordinates_rectangles)
            )
    return schemas.SpotInDBBase(
        camera_id=items.camera_id,
        name_spot=items.name_spot,
        zone_id=items.zone_id,
        coordinates_rectangles=coordinates_rectangles,
        # This id,created,modified lates record save in DB
        created=items.created,
        id=items.id,
        modified=items.modified,
    )


async def update_status(
    db: AsyncSession, spot_in: schemas.SpotUpdateStatus
) -> schemas.SpotUpdateStatus:
    camera = await crud.equipment_repo.one_equipment(
        db, serial_number=spot_in.camera_serial
    )
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    check_spot = await crud.spot_repo.one_spot(
        db,
        input_camera_id=camera.id,
        input_number_spot=spot_in.number_spot,
    )
    if not check_spot:
        raise exc.ServiceFailure(
            detail="line's camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )
    # price_ids, total_count = await price_repo.get_multi_with_filters(
    #     db, filters=ReadPricesParams(zone_id=check_spot.zone_id)
    # )

    # max_priority = float("inf")
    # max_priority_obj = None
    # for priority_price_ids in price_ids:
    #     for check_priority in priority_price_ids.pricings:
    #         if check_priority.priority < max_priority:
    #             max_priority = check_priority.priority
    #             max_priority_obj = priority_price_ids
    price = await get_main_price(db)
    if (
        spot_in.status.value == spotsSchemas.Status.full.value
        or spot_in.status.value == spotsSchemas.Status.entranceDoor.value
        or spot_in.status.value == spotsSchemas.Status.exitDoor.value
    ):

        plate_in = schemas.PlateCreate(
            plate=spot_in.plate,
            record_time=datetime.now().isoformat(),
            lpr_image_id=(
                spot_in.lpr_image_id if spot_in.lpr_image_id else None
            ),
            plate_image_id=(
                spot_in.plate_image_id if spot_in.plate_image_id else None
            ),
            spot_id=check_spot.id,
            zone_id=check_spot.zone_id,
            camera_id=camera.id,
            type_status_spot=spot_in.status,
            price_model_id=price.id,
        )

        celery_app.send_task(
            "add_plates",
            args=[jsonable_encoder(plate_in)],
        )

    check_spot.plate = spot_in.plate
    check_spot.status = spot_in.status
    check_spot.lpr_image_id = spot_in.lpr_image_id
    check_spot.plate_image_id = spot_in.plate_image_id
    check_spot.latest_time_modified = datetime.now()
    return await crud.spot_repo.update(db, db_obj=check_spot)


async def get_status(
    db: AsyncSession,
    params: spotsSchemas.ParamsSpotStatus,
):
    spot_details = []
    spots = await crud.spot_repo.get_multi(db)
    for spot in spots:
        camera_name = await crud.equipment_repo.get(db, id=spot.camera_id)
        zone_name = await crud.zone_repo.get(db, id=spot.zone_id)
        spot_details.append(
            SpotInfo(
                id=spot.id,
                camera_name=camera_name.serial_number,
                name_spot=spot.name_spot,
                zone_name=zone_name.name,
                coordinates_rectangles=SpotInfoCoordinate(
                    percent_rotation_rectangle_big=spot.percent_rotation_rectangle_small,
                    percent_rotation_rectangle_small=spot.percent_rotation_rectangle_small,
                    number_spot=spot.number_spot,
                    coordinates_rectangle_big=spot.coordinates_rectangle_big,
                    coordinates_rectangle_small=spot.coordinates_rectangle_small,
                    status=spot.status,
                    plate=spot.plate,
                    latest_time_modified=spot.latest_time_modified,
                    lpr_image_id=spot.lpr_image_id,
                    plate_image_id=spot.plate_image_id,
                ),
            )
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


async def get_details_spot_by_camera(db: AsyncSession, camera_serial: str):
    camera = await crud.equipment_repo.one_equipment(
        db, serial_number=camera_serial
    )
    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.operation_failed,
        )

    # find line's camera
    spot_lines = await crud.spot_repo.get_multi_with_filters(
        db, input_camera_id=camera.id
    )

    coordinate_details = []
    for line in spot_lines:
        coordinate_details.append(
            spotsSchemas.CoordinateSpotsByCamera(
                percent_rotation_rectangle_small=line.percent_rotation_rectangle_small,
                percent_rotation_rectangle_big=line.percent_rotation_rectangle_big,
                number_spot=line.number_spot,
                status=line.status,
                lpr_image_id=line.lpr_image_id,
                plate_image_id=line.plate_image_id,
                coordinates_rectangle_big=line.coordinates_rectangle_big,
                coordinates_rectangle_small=line.coordinates_rectangle_small,
                zone_id=line.zone_id,
                name_spot=line.name_spot,
            )
        )
    return spotsSchemas.SpotsByCamera(
        camera_id=camera.id, coordinates_rectangles=coordinate_details
    )


async def get_details_spot_by_zone_id(
    db: AsyncSession,
    zone_id: int,
    size: int = None,
    page: int = None,
    asc: bool = True,
):

    spots = await crud.spot_repo.get_multi_with_filters(
        db, input_zone_id=zone_id
    )
    all_spots_zone = []

    for spot in spots:
        camera_name = await crud.equipment_repo.get(db, id=spot.camera_id)
        zone_name = await crud.zone_repo.get(db, id=spot.zone_id)
        all_spots_zone.append(
            SpotInfo(
                id=spot.id,
                camera_name=camera_name.serial_number,
                name_spot=spot.name_spot,
                zone_name=zone_name.name,
                coordinates_rectangles=SpotInfoCoordinate(
                    percent_rotation_rectangle_big=spot.percent_rotation_rectangle_small,
                    percent_rotation_rectangle_small=spot.percent_rotation_rectangle_small,
                    number_spot=spot.number_spot,
                    coordinates_rectangle_big=spot.coordinates_rectangle_big,
                    coordinates_rectangle_small=spot.coordinates_rectangle_small,
                    status=spot.status,
                    plate=spot.plate,
                    latest_time_modified=spot.latest_time_modified,
                    lpr_image_id=spot.lpr_image_id,
                    plate_image_id=spot.plate_image_id,
                ),
            )
        )
    if size is not None:  # limit
        all_spots_zone = all_spots_zone[:size]

    if page is not None:  # skip
        all_spots_zone = all_spots_zone[::page]

    if asc:
        all_spots_zone.reverse()

    return PaginatedContent(
        data=all_spots_zone,
        total_count=len(all_spots_zone),
        size=size,
        page=page,
    )
