from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceFailure
from app.parking.models import PlateRule, Rule, ZoneRule
from app.parking.repo import (
    parkingzone_repo,
    platerule_repo,
    rule_repo,
    zonerule_repo,
)
from app.parking.schemas import rule as schemas
from app.utils import MessageCodes, PaginatedContent


async def read_rules(
    db: AsyncSession, params: schemas.ReadRulesParams
) -> PaginatedContent[list[schemas.Rule]]:
    rules, total_count = await rule_repo.get_multi_with_filters(
        db, filters=params.db_filters
    )
    return PaginatedContent(
        data=rules,
        total_count=total_count,
        size=params.size,
        page=params.page,
    )


async def create_rule(
    db: AsyncSession,
    rule_data: schemas.RuleCreate,
) -> Rule:
    filters = schemas.ReadRulesFilter(
        name_fa__eq=rule_data.name_fa,
        limit=1,
    )
    rule_exists, _ = await rule_repo.get_multi_with_filters(
        db, filters=filters
    )
    if rule_exists:
        raise ServiceFailure(
            detail="Duplicate name",
            msg_code=MessageCodes.duplicate_name,
        )
    rule_data_create = rule_data.model_dump(exclude="zone_ids")
    rule = await rule_repo.create(db, obj_in=rule_data_create, commit=False)
    for zone_id in rule_data.zone_ids:
        parkingzone = await parkingzone_repo.get(db, id=zone_id)
        if not parkingzone:
            raise ServiceFailure(
                detail=f"ParkingZone [{zone_id}] Not Found",
                msg_code=MessageCodes.not_found,
            )
        zonerule_create = schemas.ZoneRuleCreate(
            zone_id=zone_id, rule_id=rule.id
        )
        await zonerule_repo.create(db, obj_in=zonerule_create, commit=False)
    await db.commit()
    return rule


async def set_zone_rule(
    db: AsyncSession, rules: schemas.SetZoneRuleInput
) -> list[ZoneRule]:
    created_rules: list[ZoneRule] = []
    rule = await rule_repo.get(db, id=rules.rule_id)
    if not rule:
        raise ServiceFailure(
            detail="Rule Not Found",
            msg_code=MessageCodes.not_found,
        )
    for zone_id in rules.zone_ids:
        zone = await parkingzone_repo.get(db, id=zone_id)
        if not zone:
            raise ServiceFailure(
                detail=f"ParkingZone [{zone_id}] Not Found",
                msg_code=MessageCodes.not_found,
            )
        rule_exists = await zonerule_repo.find(
            db, rule_id=rule.id, zone_id=zone_id
        )
        if rule_exists:
            created_rules.append(rule_exists)
            continue
        zonerule_data = schemas.ZoneRuleCreate(
            rule_id=rule.id, zone_id=zone_id
        )
        zonerule = await zonerule_repo.create(db, obj_in=zonerule_data)
        created_rules.append(zonerule)
    return created_rules


async def set_plate_rule(
    db: AsyncSession, rules: schemas.SetPlateRuleInput
) -> list[PlateRule]:
    created_rules: list[PlateRule] = []
    rule = await rule_repo.get(db, id=rules.rule_id)
    if not rule:
        raise ServiceFailure(
            detail="Rule Not Found",
            msg_code=MessageCodes.not_found,
        )
    for plate in rules.plates:
        rule_exists = await platerule_repo.find(
            db, rule_id=rule.id, plate=plate
        )
        if rule_exists:
            created_rules.append(rule_exists)
            continue
        platerule_data = schemas.PlateRuleCreate(rule_id=rule.id, plate=plate)
        platerule = await platerule_repo.create(db, obj_in=platerule_data)
        created_rules.append(platerule)
    return created_rules
