import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app import utils
from app.core import exceptions as exc
from app.parking import repo
from app.parking import schemas as parking_schemas
from app.pricing.repo import price_repo
from fastapi.encoders import jsonable_encoder
from pydantic import TypeAdapter
from app.crud.crud_record import record as curdRecord
from app.schemas.record import StatusRecord

logger = logging.getLogger(__name__)


async def read_zone(
    db: AsyncSession,
    params: parking_schemas.ZonePramsFilters,
) -> utils.PaginatedContent[list[parking_schemas.Zone]]:
    zones, total_count = await repo.zone_repo.get_multi_by_filter(
        db, params=params
    )
    for zone in zones:
        await set_children_ancestors_capacity(db, zone)

    return utils.PaginatedContent(
        data=zones, total_count=total_count, size=params.size, page=params.page
    )


async def set_children_ancestors_capacity(
    db: AsyncSession, zone: parking_schemas.Zone
):
    zone.children = await get_children(db, zone)
    zone.ancestors = await get_ancestors(db, zone)

    total_count_full = await curdRecord.get_count_capacity(
        db, zone=zone, status_in=StatusRecord.unfinished.value
    )
    zone.full = total_count_full
    zone.empty = (
        (zone.capacity - total_count_full)
        if total_count_full
        else zone.capacity
    )
    zone.unknown = await curdRecord.get_count_capacity(
        db, zone=zone, status_in=StatusRecord.unknown.value
    )
    return zone


async def get_children(
    db: AsyncSession, zone: parking_schemas.Zone, max_depth: int = 8
):
    all_children = {zone.id}

    to_search = {zone.id}

    for _ in range(max_depth):
        children = await repo.zone_repo.get_multi_child(db, ids=to_search)
        if all(child.id in all_children for child in children):
            break
        to_search = set()
        for child in children:
            if child.id not in all_children:
                to_search.add(child.id)
                all_children.add(child.id)
    return all_children - {zone.id}


async def get_ancestors(
    db: AsyncSession, zone: parking_schemas.Zone, max_depth: int = 8
):
    if zone.parent_id is None:
        return []
    all_ancestors = {zone.parent_id}

    to_search = {zone.parent_id}

    for _ in range(max_depth):
        ancestors = await repo.zone_repo.get_multi_ancestor(db, ids=to_search)
        if all(ancestor.parent_id in all_ancestors for ancestor in ancestors):

            break
        to_search = set()
        for ancestor in ancestors:
            if (
                ancestor.parent_id not in all_ancestors
                and ancestor.parent_id is not None
            ):
                to_search.add(ancestor.parent_id)
                all_ancestors.add(ancestor.parent_id)
    return all_ancestors


async def create_zone(
    db: AsyncSession,
    zones_in: list[parking_schemas.ZoneCreate],
) -> list[parking_schemas.Zone]:

    zone_list = []
    for zone in zones_in:
        zone_exist = await repo.zone_repo.get_by_name(db, name=zone.name)
        if zone_exist:
            raise exc.ServiceFailure(
                detail="zone with this name already exists",
                msg_code=utils.MessageCodes.duplicate_zone_name,
            )

        if zone.parent_id is not None:
            parent_zone = await repo.zone_repo.get(db, id=zone.parent_id)
            if not parent_zone:
                raise exc.ServiceFailure(
                    detail="Parking Not Found",
                    msg_code=utils.MessageCodes.not_found,
                )

        zone_create = await repo.zone_repo.create(
            db,
            obj_in=zone,
        )

        zone_list.append(jsonable_encoder(zone_create))
    return zone_list


async def set_price(
    db: AsyncSession,
    zone_id: int,
    zoneprice_data: parking_schemas.SetZonePriceInput,
    commit: bool = True,
) -> parking_schemas.ZonePrice:
    zone = await repo.zone_repo.get(db, id=zone_id)
    if not zone:
        raise exc.ServiceFailure(
            detail="Zone Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    price = await price_repo.get(db, id=zoneprice_data.price_id)
    if not price:
        raise exc.ServiceFailure(
            detail="Price Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    is_duplicate = await repo.zoneprice_repo.pricing_exists(
        db,
        zone_id=zone.id,
        price_id=price.id,
        priority=zoneprice_data.priority,
    )
    if is_duplicate:
        raise exc.ServiceFailure(
            detail="This pricing already exists",
            msg_code=utils.MessageCodes.duplicate_zone_pricing,
        )

    zoneprice_create = parking_schemas.ZonePriceCreate(
        zone_id=zone.id, price_id=price.id, priority=zoneprice_data.priority
    )
    zone_price = await repo.zoneprice_repo.create(
        db, obj_in=zoneprice_create, commit=commit
    )
    return zone_price
