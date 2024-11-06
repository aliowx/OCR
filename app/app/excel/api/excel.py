from fastapi import APIRouter, Depends, Query
from app import models
from sqlalchemy.ext.asyncio import AsyncSession
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated
from app.api import deps
from app.utils import generate_excel
from datetime import datetime
from fastapi.responses import StreamingResponse
from app import crud
import json
import logging

router = APIRouter()
namespace = "plate"
logger = logging.getLogger(__name__)


@router.post("/download")
async def download_excel(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    *,
    data: str = Query(...),
    excel_name: str = f"{datetime.now().date()}",
) -> StreamingResponse:
    """
    Retrieve plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    data = await crud.record.get_multi(db, limit=None)
    print(data)
    # if data is not None:
    #     data = json.loads(data)
    # data_list = [data] if isinstance(data, dict) else data
    file = generate_excel.get_excel_file_response(
        data=data, title=excel_name
    )
    return file
