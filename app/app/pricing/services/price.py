from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ServiceFailure
from app.parking.repo import parking_repo
from app.parking.schemas import SetZonePriceInput
from app.parking.services import zone as zone_services
from app.pricing import schemas as price_schemas
from app.pricing.repo import price_repo
from app.utils import MessageCodes, PaginatedContent


async def create_price(
    db: AsyncSession, price_in: price_schemas.PriceCreate
) -> price_schemas.Price:

    get_price, total_count = await price_repo.get_multi_with_filters(
        db,
        filters=price_schemas.ReadPricesParams(
            name=price_in.name,
        ),
    )
    if get_price:
        raise ServiceFailure(
            detail="This name or name_fa exist",
            msg_code=MessageCodes.duplicate_name,
        )

    price_data_create = price_in.model_copy(
        update={"zone_ids": None, "priority": None}
    )
    price = await price_repo.create(
        db,
        obj_in=price_data_create.model_dump(mode="json", exclude_none=True),
        commit=False,
    )
    for zone_id in price_in.zone_ids:
        zoneprice_data = SetZonePriceInput(
            price_id=price.id, priority=price_in.priority
        )
        await zone_services.set_price(
            db,
            zone_id=zone_id,
            zoneprice_data=zoneprice_data,
            commit=False,
        )
    await db.commit()
    return price


async def read_prices(
    db: AsyncSession, params: price_schemas.ReadPricesParams
) -> PaginatedContent[list[price_schemas.Price]]:
    prices, total_count = await price_repo.get_multi_with_filters(
        db, filters=params
    )
    price_list = []
    for price, zone in prices:
        price.zone_name = zone.name
        price_list.append(price)
    return PaginatedContent(
        data=price_list,
        total_count=total_count,
        size=params.size,
        page=params.page,
    )
