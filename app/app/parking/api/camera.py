import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType
from app.parking import schemas as cameraSchema

router = APIRouter()
namespace = "camera"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_camera(
    db: AsyncSession = Depends(deps.get_db_async),
    params: cameraSchema.ParamsCamera = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.GetCamera]:
    """
    Get All Camera.
    """
    cameras = await crud.camera_repo.find_cameras(db, params=params)
    return APIResponse(
        schemas.GetCamera(items=cameras, all_items_count=len(cameras))
    )


@router.post("/")
async def create_camera(
    camera_in: schemas.CameraCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Camera]:
    """
    Create New Camera.
    """
    camera_exist = await crud.camera_repo.find_cameras(
        db, input_camera_code=camera_in.camera_code
    )

    if camera_exist:
        raise exc.ServiceFailure(
            detail="The camera with this camera_code already exists in the system.",
            msg_code=utils.MessageCodes.bad_request,
        )
    camera_main_image = await crud.image.get(db, id=camera_in.image_id)

    if not camera_main_image:
        raise exc.ServiceFailure(
            detail="Camera image not found.",
            msg_code=utils.MessageCodes.not_found,
        )

    return APIResponse(await crud.camera_repo.create(db, obj_in=camera_in))


@router.get("/{id}")
async def get_camera_by_id(
    id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Camera]:
    """
    Get One Camera.
    """

    camera = await crud.camera_repo.get(db, id=id)

    if not camera:
        raise exc.ServiceFailure(
            detail="The camera not created in the system.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(camera)


@router.put("/{id}")
async def update_camera(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
    camera_in: schemas.CameraUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Camera]:
    """
    Update Camera.
    """
    camera = await crud.camera_repo.get(db, id=id)
    if not camera:
        raise exc.ServiceFailure(
            detail="The camera not exist in the system.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(
        await crud.camera_repo.update(db, db_obj=camera, obj_in=camera_in)
    )


@router.delete("/{id}")
async def delete_camera(
    id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Camera]:
    """
    Delete camera
    """
    camera = await crud.camera_repo.get(db, id=id)
    if not camera:
        raise exc.ServiceFailure(
            detail="The camera not exist in the system.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(await crud.camera_repo._remove_async(db, id=id))


@router.post("/upload_photo")
async def upload_photo(
    camera_code: str,
    image_id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
):

    camera = await crud.camera_repo.one_camera(
        db, input_camera_code=camera_code
    )

    if not camera:
        raise exc.ServiceFailure(
            detail="camera not exist",
            msg_code=utils.MessageCodes.not_found,
        )
    camera.image_id = image_id
    return APIResponse(await crud.camera_repo.update(db, db_obj=camera))
