from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas


async def calculator_price(
    db: AsyncSession,
    *,
    score: float = None,
    skip: int = 0,
    limit: int = 100,
    asc: bool = True,
    input_ocr: str = None
):
    records = await crud.record.find_records(
        db=db,
        input_score=score,
        input_ocr=input_ocr,
        skip=skip,
        limit=limit,
        asc=asc,
    )

    weekdays = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    for t in range(len(records[0])):
        item_record = records[0][t]

        # Calculation of parkinglot time
        item_record.parkinglot_time = str(
            item_record.end_time - item_record.start_time
        )
        # Calculation hours, conversion minutes and seconds to hours
        hours, minutes, seconds = map(
            float, item_record.parkinglot_time.split(":")
        )
        minutes = minutes / 60 if minutes > 0 else 0
        seconds = seconds / 3600 if seconds > 0 else 0
        total_hours = hours + minutes + seconds

        if item_record.price_model["price_type"] == "weekly":
            price_weekly_day = weekdays[item_record.end_time.weekday()]
            item_record.parkinglot_price = (
                total_hours * item_record.price_model[price_weekly_day]
            )
        if item_record.price_model["price_type"] == "zone":
            item_record.parkinglot_price = (
                total_hours * item_record.price_model["price"]
            )

    return schemas.GetRecords(items=records[0], all_items_count=records[1])
