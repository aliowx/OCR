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

logger = logging.getLogger(__name__)


async def read_zone(
    db: AsyncSession,
    params: parking_schemas.ZonePramsFilters,
) -> utils.PaginatedContent[list[parking_schemas.Zone]]:
    zones, total_count = await repo.zone_repo.get_multi_by_filter(
        db, params=params
    )
    for zone in zones:
        record, total_count_record = await curdRecord.find_records(
            db, input_zone_id=zone.id, input_status_record="unfinished"
        )
        zone.empty = (
            (zone.capacity - total_count_record)
            if total_count_record
            else zone.capacity
        )
        zone.full = total_count_record if total_count_record else 0

    return utils.PaginatedContent(
        data=zones, total_count=total_count, size=params.size, page=params.page
    )


async def create_zone(
    db: AsyncSession,
    zone_input: parking_schemas.ZoneCreate,
) -> parking_schemas.Zone:

    zone = await repo.zone_repo.get_by_name(db, name=zone_input.name)
    if zone:
        raise exc.ServiceFailure(
            detail="zone with this name already exists",
            msg_code=utils.MessageCodes.duplicate_zone_name,
        )

    zone = await repo.zone_repo.create(db, obj_in=zone_input)
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
    all_ancesstors = {zone.parent_id}

    to_search = {zone.parent_id}

    for _ in range(max_depth):
        ancesstors = await repo.zone_repo.get_multi_ancesstor(
            db, ids=to_search
        )
        if all(
            ancesstor.parent_id in all_ancesstors for ancesstor in ancesstors
        ):

            break
        to_search = set()
        for ancesstor in ancesstors:
            if (
                ancesstor.parent_id not in all_ancesstors
                and ancesstor.parent_id is not None
            ):
                to_search.add(ancesstor.parent_id)
                all_ancesstors.add(ancesstor.parent_id)
    return all_ancesstors


async def create_sub_zone(
    db: AsyncSession,
    zone_input: parking_schemas.SubZoneCreate,
) -> list[parking_schemas.Zone]:

    for sub in zone_input.sub_zone:
        zone = await repo.zone_repo.get_by_name(db, name=sub.name)
        if zone:
            raise exc.ServiceFailure(
                detail="zone with this name already exists",
                msg_code=utils.MessageCodes.duplicate_zone_name,
            )

    parent_zone = None
    if zone_input.parent_id is not None:
        parent_zone = await repo.zone_repo.get(db, id=zone_input.parent_id)
        if not parent_zone:
            raise exc.ServiceFailure(
                detail="Parking Not Found",
                msg_code=utils.MessageCodes.not_found,
            )
    sub_zone_list = []
    adapter = TypeAdapter(parking_schemas.Zone)
    for multi_sub in zone_input.sub_zone:
        zone = await repo.zone_repo.create(
            db,
            obj_in=parking_schemas.ZoneBase(
                name=multi_sub.name,
                tag=multi_sub.tag,
                parent_id=zone_input.parent_id,
                floor_name=multi_sub.floor_name,
                floor_number=multi_sub.floor_number,
            ),
        )

        sub_zone_list.append(
            jsonable_encoder(
                adapter.validate_python(zone, from_attributes=True)
            )
        )
    return sub_zone_list


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
