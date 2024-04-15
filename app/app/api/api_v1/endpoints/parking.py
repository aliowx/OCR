import logging
from app.utils import APIResponse, APIResponseType
from typing import Any
from fastapi import APIRouter, Depends
from app import exceptions as exc
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, schemas, utils
from app.api import deps
from app.core.celery_app import celery_app
from datetime import datetime

router = APIRouter()
namespace = "parking"
logger = logging.getLogger(__name__)


@router.post("/")
async def create_lines_parking(
    parking_in: schemas.ParkingCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Create new line Parking.
    """

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
        )
        items = await crud.parking.create(db, obj_in=new_obj)
        if items:
            reverse_coordinates_rectangles = {
                "number_line": new_obj.number_line,
                "coordinates_rectangle_big": new_obj.coordinates_rectangle_big,
                "coordinates_rectangle_small": new_obj.coordinates_rectangle_small,
                "percent_rotation_rectangle_small": new_obj.percent_rotation_rectangle_small,
                "percent_rotation_rectangle_big": new_obj.percent_rotation_rectangle_big,
            }
            coordinates_rectangles.append(reverse_coordinates_rectangles)
    # this schemas show result
    return APIResponse(
        schemas.ParkingInDBBase(
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
    )


# this endpoint for update status
@router.post("/update_status")
async def update_status(
    parking_in: schemas.ParkingUpdateStatus,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[dict]:

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
    return APIResponse(await crud.parking.update(db, db_obj=check))


# get all status and detail parking
@router.get("/check_status")
async def checking_status(
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
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
                        "status": parking.status,
                        "ocr": parking.ocr,
                        "latest_time_modified": parking.latest_time_modified,
                        "lpr_img": parking.lpr_img_id,
                        "ocr_img": parking.ocr_img_id,
                    }
                ],
            }
        )

    return APIResponse(parking_details)


# this endpoint get all line by camera code
@router.get("/{camera_code}")
async def get_detail_camera(
    camera_code: str,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.ParkingCreate]:

    # check camera exist
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
            }
        )

    return APIResponse(
        schemas.ParkingCreate(
            camera_id=camera.id,
            floor_number=parking_lines[0].floor_number,
            floor_name=parking_lines[0].floor_name,
            name_parking=parking_lines[0].name_parking,
            coordinates_rectangles=coordinate_details,
        )
    )
