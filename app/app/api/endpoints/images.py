import io
import logging
import base64
import json
from typing import Any, Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app import crud, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, storage
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from app.parking.repo import equipment_repo

router = APIRouter()
logger = logging.getLogger(__name__)

namespace = "images"


def validate_camera(db: AsyncSession, camera_id: int) -> None:
    """Check if the camera exists."""
    if not equipment_repo.get(db, id=camera_id):
        raise exc.ServiceFailure(
            detail="Camera Not Found",
            msg_code=utils.MessageCodes.not_found,
        )


def parse_metadata(metadata: str | None) -> dict | None:
    """Parse metadata JSON string into a dictionary."""
    return json.loads(metadata) if metadata else None


async def handle_image_storage(
    save_as: schemas.image.ImageSaveAs,
    file_in: UploadFile,
    metadata: dict | None,
    db: AsyncSession,
    camera_id: int | None,
) -> Any:
    """Handle image storage logic based on save_as type."""
    file_content = await file_in.read()
    
    if save_as == schemas.image.ImageSaveAs.minio:
        file_bytes = io.BytesIO(file_content)
        client = storage.get_client(name=save_as)
        path_file = client.upload_file(
            content=file_bytes,
            name=file_in.filename,
            size=file_in.size,
            metadata=metadata,
        )
        obj_in = schemas.image.ImageCreate(
            path_image=path_file, additional_data=metadata, camera_id=camera_id
        )
        return await crud.image.create_path(db, obj_in=obj_in.model_dump())

    elif save_as == schemas.image.ImageSaveAs.database:
        file_base64 = base64.b64encode(file_content).decode("utf-8")
        obj_in = schemas.image.ImageCreate(
            image=file_base64, additional_data=metadata, camera_id=camera_id
        )
        return await crud.image.create_base64(db, obj_in=obj_in.model_dump())

    raise exc.ServiceFailure(
        detail="Invalid save_as option",
        msg_code=utils.MessageCodes.invalid_input,
    )


@router.post("/")
async def create_image(
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    metadata: str = Query(),
    camera_id: int | None = None,
    save_as: schemas.image.ImageSaveAs | None = None,
    file_in: UploadFile,
) -> APIResponseType[Any]:
    """
    Create a new image.

    User access: [ADMINISTRATOR]
    """
    if camera_id is not None:
        await validate_camera(db, camera_id)

    metadata_dict = parse_metadata(metadata)
    image = await handle_image_storage(save_as, file_in, metadata_dict, db, camera_id)
    return APIResponse(image)


@router.get("/{id}")
async def read_image(
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    id: int = None,
) -> APIResponseType[schemas.ImageBase64InDB]:
    """
    Get an image by ID.

    User access: [ADMINISTRATOR]
    """
    image = await crud.image.get_base64(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Image Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(image)


@router.get("/binary/{id}")
async def read_image_binary(
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    id: int = None,
) -> StreamingResponse:
    """
    Get an image in binary format by ID.

    User access: [ADMINISTRATOR]
    """
    image = await crud.image.get(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Image Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    return StreamingResponse(io.BytesIO(image.image), media_type="image/png")


@router.get("/get-image-minio/{id}")
async def read_minio(
    _: Annotated[
        bool,
        Depends(RoleChecker(
            allowed_roles=[
                UserRoles.ADMINISTRATOR,
                UserRoles.PARKING_MANAGER,
                UserRoles.APPS,
            ]
        )),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    id: int = None,
) -> StreamingResponse:
    """
    Get an image stored in MinIO by ID.

    User access: [ADMINISTRATOR, PARKING_MANAGER, APPS]
    """
    image = await crud.image.get(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Image Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    bucket_name, path_image = image.path_image.split("/", 1)
    client = storage.get_client(name=schemas.image.ImageSaveAs.minio)
    file = client.download_file(bucket_name=bucket_name, file_name=path_image)
    return StreamingResponse(io.BytesIO(file.read()), media_type="image/png")


@router.delete("/{id}")
async def delete_image(
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: Session = Depends(deps.get_db),
    id: int = None,
) -> APIResponseType[schemas.ImageBase64InDB]:
    """
    Delete an image by ID.

    User access: [ADMINISTRATOR]
    """
    image = crud.image.get(db=db, id=id)
    if not image:
        raise exc.ServiceFailure(
            detail="Image Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    deleted_image = crud.image.remove_base64(db=db, id=id)
    return APIResponse(deleted_image)
