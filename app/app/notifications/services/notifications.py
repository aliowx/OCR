from sqlalchemy.ext.asyncio import AsyncSession
from app.plate.schemas.plate import ParamsPlate, PlateCreate
from app.notifications.repo import notifications_repo
from fastapi import UploadFile
import io
import pandas as pd


async def get_multi_notifications_by_filter(db: AsyncSession, *, params: ParamsPlate):

    notifications, total_count = await notifications_repo.get_multi_by_filter(
        db, params=params
    )

    return notifications, total_count


