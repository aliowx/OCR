import logging
import io
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, utils
from app.api import deps
from starlette.responses import StreamingResponse
from app import exceptions as exc
from app.utils import APIResponse, APIResponseType


router = APIRouter()
namespace = "images"
logger = logging.getLogger(__name__)


@router.post("/")
async def create_image(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    image_in: schemas.ImageCreateBase64,
) -> APIResponseType[schemas.ImageBase64InDB]:
    """
    Create new image.
    """
    image = await crud.image.create_base64(db=db, obj_in=image_in)
    return APIResponse(image)


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
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> APIResponseType[schemas.ImageBase64InDB]:
    """
    Get image by ID.
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
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> APIResponseType[Any]:
    """
    Get binary image by ID.
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
    db: Session = Depends(deps.get_db),
    id: int,
) -> APIResponseType[schemas.ImageBase64InDB]:
    """
    Delete an image.
    """
    image = crud.image.get(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    image = crud.image.remove_base64(db=db, id=id)
    return APIResponse(image)
