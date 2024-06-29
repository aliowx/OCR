import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.report import schemas as report_schemas
from app.report import services as report_services
from app.utils import APIResponse, APIResponseType, PaginatedContent

router = APIRouter()
namespace = "report"
logger = logging.getLogger(__name__)


@router.get("/status-parking-by-zone")
async def zone_status(
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
    params: report_schemas.ReadZoneLotsParams = Depends(),
) -> APIResponseType[PaginatedContent[list[report_schemas.ZoneLots]]]:

    return APIResponse(await report_services.report_zone(db, params))


@router.get("/record-moment")
async def zone_status(
    db: AsyncSession = Depends(deps.get_db_async),
    params: report_schemas.ParamsRecordMoment = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[list[report_schemas.ZoneLots]]]:

    return APIResponse(await report_services.report_moment(db, params))
