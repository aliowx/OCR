from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.api import deps
from starlette.responses import StreamingResponse
import logging
import io

router = APIRouter()
namespace = "images"
logger = logging.getLogger(__name__)


@router.post("/", response_model=schemas.ImageBase64InDB)
async def create_image(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    image_in: schemas.ImageCreateBase64,
) -> Any:
    """
    Create new image.
    """
    image = await crud.image.create_base64(db=db, obj_in=image_in)
    return image


@router.put("/{id}", response_model=schemas.ImageBase64InDB)
async def update_image(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
    image_in: schemas.ImageUpdateBase64,
) -> Any:
    """
    Update a Image.
    """
    image = await crud.image.get_base64(db=db, id=id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image = await crud.image.update_base64(
        db=db, db_obj=image, obj_in=image_in
    )
    return image


@router.get("/{id}", response_model=schemas.ImageBase64InDB)
async def read_image(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> Any:
    """
    Get image by ID.
    """
    image = await crud.image.get_base64(db=db, id=id)
    if not image:
        raise HTTPException(status_code=404, detail="Plate Image not found")
    return image


@router.get("/binary/{id}", response_model=Any)
async def read_image_binary(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> Any:
    """
    Get binary image by ID.
    """
    image = await crud.image.get(db=db, id=id)
    if not image:
        raise HTTPException(status_code=404, detail="Plate Image not found")
    return StreamingResponse(io.BytesIO(image.image), media_type="image/png")


@router.get("/details/{id}", response_model=schemas.ImageDetails)
async def read_image_details(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> Any:
    """
    Get details of an image by ID.
    """
    image = await crud.image.get(db=db, id=id)
    if not image:
        raise HTTPException(status_code=404, detail="Plate Image not found")
    # del image.image  # TODO: must be corrected
    return image


@router.delete("/{id}", response_model=schemas.ImageBase64InDB)
def delete_image(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Delete an image.
    """
    image = crud.image.get(db=db, id=id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image = crud.image.remove_base64(db=db, id=id)
    return image
