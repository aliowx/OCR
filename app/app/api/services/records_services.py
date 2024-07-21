from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.pricing.repo import price_repo


async def calculator_price(db: AsyncSession, *, params: schemas.ParamsRecord):
    records = await crud.record.find_records(
        db=db,
        input_score=params.input_score,
        input_plate=params.input_plate,
        input_end_time_max=params.input_end_time_max,
        input_end_time_min=params.input_end_time_min,
        input_start_time_max=params.input_start_time_max,
        input_start_time_min=params.input_start_time_min,
        skip=params.skip,
        limit=None,
        asc=params.asc,
    )

    # weekdays = [
    #     "monday",
    #     "tuesday",
    #     "wednesday",
    #     "thursday",
    #     "friday",
    #     "saturday",
    #     "sunday",
    # ]

    for record in range(len(records[0])):
        item_record = records[0][record]
        get_price = await price_repo.get(db, id=item_record.price_model_id)

        # Calculation of spot time
        item_record.total_time = str(
            item_record.end_time - item_record.start_time
        )
        # Calculation hours, conversion minutes and seconds to hours
        hours, minutes, seconds = map(float, item_record.total_time.split(":"))
        minutes = minutes / 60 if minutes > 0 else 0
        seconds = seconds / 3600 if seconds > 0 else 0
        total_hours = hours + minutes + seconds

        # TODO set daily_price and penalti_price
        item_record.total_price = (
            total_hours * get_price.hourly_fee + get_price.entrance_fee
        )

    return schemas.GetRecords(items=records[0], all_items_count=records[1])
