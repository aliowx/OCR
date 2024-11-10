import io
import logging
from typing import Any
from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
import base64
from app import crud, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, storage
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated
from app.parking.repo import equipment_repo
import json


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
    metadata: str = Query(),
    camera_id: int | None = None,
    save_as: schemas.image.ImageSaveAs | None = None,
    file_in: UploadFile,
) -> APIResponseType[Any]:
    """
    Create new image.
    user access to this [ ADMINISTRATOR ]
    """
    if camera_id is not None:
        camera_exist = await equipment_repo.get(db, id=camera_id)
        if not camera_exist:
            raise exc.ServiceFailure(
                detail="Camera Not Found",
                msg_code=utils.MessageCodes.not_found,
            )

    if metadata is not None:
        metadata = json.loads(metadata)

    if save_as == schemas.image.ImageSaveAs.minio:
        file_content = await file_in.read()
        file_bytes = io.BytesIO(file_content)
        client = storage.get_client(name=save_as)
        path_file = client.upload_file(
            content=file_bytes,
            name=file_in.filename,
            size=file_in.size,
            metadata=metadata,
        )
        obj_in = schemas.image.ImageCreate(
            path_image=path_file, additional_data=metadata
        )
        if camera_id is not None:
            obj_in.camera_id = camera_id
        image = await crud.image.create_path(db, obj_in=obj_in.model_dump())

    elif save_as == schemas.image.ImageSaveAs.database:
        file_content = await file_in.read()
        file_base64 = base64.b64encode(file_content).decode("utf-8")
        obj_in = schemas.image.ImageCreate(
            image=file_base64, additional_data=metadata
        )
        if camera_id is not None:
            obj_in.camera_id = camera_id
        image = await crud.image.create_base64(
            db=db, obj_in=obj_in.model_dump()
        )
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


@router.get("/get-image-minio/{id}")
async def read_minio(
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
    *,
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
    bucket_name, path_image = image.path_image.split("/", 1)
    client = storage.get_client(name=schemas.image.ImageSaveAs.minio)
    file = client.download_file(bucket_name=bucket_name, file_name=path_image)
    read_file = file.read()
    return StreamingResponse(io.BytesIO(read_file), media_type="image/png")


@router.delete("/{id}")
def delete_image(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
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
