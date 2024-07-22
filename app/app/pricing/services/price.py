from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceFailure
from app.parking.repo import parking_repo
from app.parking.schemas import SetZonePriceInput
from app.parking.services import zone as zone_services
from app.pricing import schemas as price_schemas
from app.pricing.repo import price_repo
from app.utils import MessageCodes, PaginatedContent


async def create_price(
    db: AsyncSession, price_data: price_schemas.PriceCreate
) -> price_schemas.Price:

    price_data_create = price_data.model_copy(
        update={"zone_ids": None, "priority": None}
    )
    price = await price_repo.create(
        db,
        obj_in=price_data_create.model_dump(exclude_none=True),
        commit=False,
    )
    for zone_id in price_data.zone_ids:
        zoneprice_data = SetZonePriceInput(
            price_id=price.id, priority=price_data.priority
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
    return PaginatedContent(
        data=prices,
        total_count=total_count,
        size=params.size,
        page=params.page,
    )

async def get_main_price(
        db: AsyncSession
) -> price_schemas.Price:
    price = await price_repo.get_multi(db)
    if not price:
        return None
    return price[0]
