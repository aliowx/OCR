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
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated
from app.parking.schemas import Zone
from app.parking.repo import zone_repo


router = APIRouter()
namespace = "price"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_price(
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
    current_user: models.User = Depends(deps.get_current_active_user),
    *,
    params: price_schemas.ReadPricesParams = Depends(),
) -> APIResponseType[PaginatedContent[list[price_schemas.Price]]]:
    """
    Get All price.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    prices, count = await price_repo.get_multi_with_filters(db, params=params)
    return APIResponse(
        PaginatedContent(
            data=prices, total_count=count, page=params.page, size=params.size
        )
    )


@router.post("/")
async def create_price(
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
    price_in: schemas.PriceCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Price]:
    """
    Create New price.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    price_without_zone_ids = price_in.model_copy(
        update={"zone_ids": None}
    ).model_dump(exclude_none=True)
    
    price = await price_repo.create(db, obj_in=price_without_zone_ids)

    if (price_in.zone_ids is not None) and (price_in.zone_ids != []):
        for zone_id in price_in.zone_ids:
            zone = await zone_repo.get(db, id=zone_id)
            if not price:
                raise exc.ServiceFailure(
                    detail="The zone not created in the system.",
                    msg_code=utils.MessageCodes.not_found,
                )
            zone.price_id = price.id
            await zone_repo.update(db, db_obj=zone)

    return APIResponse(price)


@router.get("/{id}")
async def get_price_by_id(
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
    id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Price]:
    """
    Get One Price.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    price = await crud.price_repo.get(db, id=id)

    if not price:
        raise exc.ServiceFailure(
            detail="The price not created in the system.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(price)


@router.get("/get-zone-by-price-id/")
async def get_price_by_id(
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
    current_user: models.User = Depends(deps.get_current_active_user),
    id: int,
) -> APIResponseType[list[Zone]]:
    """
    Get zones .
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    price = await crud.price_repo.get(db, id=id)
    if not price:
        raise exc.ServiceFailure(
            detail="The price not created in the system.",
            msg_code=utils.MessageCodes.not_found,
        )

    zones = await zone_repo.get_zones_by_price_id(db, price_id=id)

    return APIResponse(zones)


@router.put("/{id}")
async def update_price(
    *,
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
    id: int,
    price_in: schemas.PriceUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Price]:
    """
    Update Price.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
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


@router.delete("/{id}")
async def delete_price(
    *,
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
    id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Price]:
    """
    Update Price.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    price = await crud.price_repo.get(db, id=id)
    if not price:
        raise exc.ServiceFailure(
            detail="The price not exist in the system.",
            msg_code=utils.MessageCodes.not_found,
        )

    return APIResponse(await crud.price_repo.remove(db, id_in=price.id))
