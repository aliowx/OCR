import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app import crud, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, storage
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "images"
logger = logging.getLogger(__name__)


@router.post("/")
async def create_image(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    file: UploadFile | None = None,
    camera_id: int,
    save_as: schemas.image.ImageSaveAs | None = None,
) -> APIResponseType[Any]:
    """
    Create new image.
    user access to this [ ADMINISTRATOR ]
    """
    if save_as is not None:
        client = storage.get_client(name=save_as)
        client.upload_file()
    else:
        image = await crud.image.create_base64(db=db, obj_in=image_in)
    return
    # return APIResponse(image)


# TODO Fix bug
# @router.put("/{id}")
# async def update_image(
#     *,
#     db: AsyncSession = Depends(deps.get_db_async),
#     id: int,
#     image_in: schemas.ImageUpdateBase64,
# ) -> APIResponseType[schemas.ImageBase64InDB]:
#     """
#     Update a Image.
#     """
#     image = await crud.image.get_base64(db=db, id=id)
#     if not image:
#         raise HTTPException(status_code=404, detail="Image not found")
#     image = await crud.image.update_base64(
#         db=db, db_obj=image, obj_in=image_in
#     )
#     return APIResponse(image)


@router.get("/{id}")
async def read_image(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> APIResponseType[schemas.ImageBase64InDB]:
    """
    Get image by ID.

    user access to this [ ADMINISTRATOR ]

    """
    image = await crud.image.get_base64(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(image)


@router.get("/binary/{id}")
async def read_image_binary(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> APIResponseType[Any]:
    """
    Get binary image by ID.

    user access to this [ ADMINISTRATOR ]

    """
    image = await crud.image.get(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    return StreamingResponse(io.BytesIO(image.image), media_type="image/png")


@router.delete("/{id}")
def delete_image(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                ]
            )
        ),
    ],
    db: Session = Depends(deps.get_db),
    id: int,
) -> APIResponseType[schemas.ImageBase64InDB]:
    """
    Delete an image.

    user access to this [ ADMINISTRATOR ]

    """
    image = crud.image.get(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    image = crud.image.remove_base64(db=db, id=id)
    return APIResponse(image)
