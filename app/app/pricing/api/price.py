import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.pricing import schemas as price_schemas
from app.pricing import services as pricing_services
from app.pricing.repo import price_repo
from app.utils import APIResponse, APIResponseType, PaginatedContent

router = APIRouter()
namespace = "price"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_price(
    db: AsyncSession = Depends(deps.get_db_async),
    params: price_schemas.ReadPricesParams = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[list[price_schemas.Price]]]:
    """
    Get All price.
    """
    prices = await pricing_services.read_prices(db, params=params)
    return APIResponse(prices)


@router.post("/")
async def create_price(
    price_in: schemas.PriceCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Price]:
    """
    Create New price.
    """
    price = await pricing_services.create_price(db, price_in=price_in)
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

    price = await crud.price_repo.get(db, id=id)

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
    price = await crud.price_repo.get(db, id=id)
    if not price:
        raise exc.ServiceFailure(
            detail="The price not exist in the system.",
            msg_code=utils.MessageCodes.not_found,
        )

    return APIResponse(
        await crud.price_repo.update(db, db_obj=price, obj_in=price_in)
    )
