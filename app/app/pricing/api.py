import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.parking.repo import parking_repo
from app.utils import APIResponse, APIResponseType

router = APIRouter()
namespace = "price"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_price(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 1000,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.GetPrice]:
    """
    Get All price.
    """
    price = await crud.price.get_multi(db, skip=skip, limit=limit)
    return APIResponse(
        schemas.GetPrice(items=price, all_items_count=len(price))
    )


@router.post("/")
async def create_price(
    price_in: schemas.PriceCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Price]:
    """
    Create New price.
    """
    if price_in.parking_id:
        parking = await parking_repo.get(db, id=price_in.parking_id)
    else:
        parking = await parking_repo.get_main_parking(db)
    if not parking:
        raise exc.ServiceFailure(
            detail="Parking not found",
            msg_code=utils.MessageCodes.not_found,
        )
    price = await crud.price.create(db, obj_in=price_in, commit=False)
    return APIResponse(price)


@router.get("/{id}")
async def get_price_by_id(
    id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Price]:
    """
    Get One Price.
    """

    price = await crud.price.get(db, id=id)

    if not price:
        raise exc.ServiceFailure(
            detail="The price not created in the system.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(price)


@router.put("/{id}")
async def update_price(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
    price_in: schemas.PriceUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Price]:
    """
    Update Price.
    """
    price = await crud.price.get(db, id=id)
    if not price:
        raise exc.ServiceFailure(
            detail="The price not exist in the system.",
            msg_code=utils.MessageCodes.not_found,
        )

    return APIResponse(
        await crud.camera.update(db, db_obj=price, obj_in=price_in)
    )


@router.delete("/{id}")
async def delete_price(
    id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Price]:
    """
    Delete Price
    """
    price = await crud.price.get(db, id=id)
    if not price:
        raise exc.ServiceFailure(
            detail="The price not exist in the system.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(await crud.price._remove_async(db, id=id))
