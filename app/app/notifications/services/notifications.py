from sqlalchemy.ext.asyncio import AsyncSession
from app.plate.schemas.plate import ParamsPlate, PlateCreate
from app.notifications.repo import notifications_repo
from fastapi import UploadFile
import io
import pandas as pd


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
    for notice in notifications:
        notice[0].plate = notice[1]
        notice[0].event = notice[2]
        notice[0].zone_name = notice[3]
        notice[0].camera_tag = notice[4]
        notice[0].status = "entrance" if notice[4] == "unfinished" else "exit"
        resualt.append(notice[0])
    return resualt, total_count
