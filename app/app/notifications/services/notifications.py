from sqlalchemy.ext.asyncio import AsyncSession
from app.plate.schemas.plate import ParamsPlate, PlateCreate
from app.notifications.repo import notifications_repo
from fastapi import UploadFile
import io
import pandas as pd
from app.schemas import TypeEvent
from app import crud
from app.models.base import EquipmentType


async def get_multi_notifications_by_filter(
    db: AsyncSession, *, params: ParamsPlate
):

    notifications, total_count = await notifications_repo.get_multi_by_filter(
        db, params=params
    )

    # notifications
    #       notice[0] -> notification
    #       notice[1] -> plate_list
    #       notice[2] -> event
    #       notice[3] -> zone_name
    #       notice[4] -> camera_tag
    #       notice[5] -> status
    resualt = []

    async def _get_camera(db, id: int):
        return (await crud.equipment_repo.get(db, id=id)).equipment_type

    for notice in notifications:
        if notice[2].camera_id is not None:
            get_type_camera = await _get_camera(db, id=notice[2].camera_id)

            if notice[2].type_event in (
                TypeEvent.exitDoor.value,
                TypeEvent.entranceDoor.value,
                TypeEvent.admin_exitRegistration_and_billIssuance.value,
                TypeEvent.admin_exitRegistration.value,
            ):
                direction = (
                    "exit"
                    if notice[2].type_event
                    in (
                        TypeEvent.exitDoor.value,
                        TypeEvent.admin_exitRegistration_and_billIssuance.value,
                        TypeEvent.admin_exitRegistration.value,
                    )
                    else "entry"
                )
            elif notice[2].type_event == TypeEvent.approaching_leaving_unknown:
                direction = notice[2].direction_info.get("direction")
                if direction is not None:
                    if direction < 0:
                        direction = (
                            "exit"
                            if get_type_camera
                            == EquipmentType.CAMERA_DIRECTION_EXIT.value
                            else "entry"
                        )
                    else:
                        direction = (
                            "entry"
                            if get_type_camera
                            == EquipmentType.CAMERA_DIRECTION_EXIT.value
                            else "exit"
                        )
                else:
                    direction = "unknown"
            else:  # sensors, etc...
                direction = "sensor_entry"
        notice[0].plate = notice[1]
        notice[0].event = notice[2]
        notice[0].zone_name = notice[3]
        notice[0].camera_tag = notice[4]
        notice[0].status = direction
        resualt.append(notice[0])
    return resualt, total_count
