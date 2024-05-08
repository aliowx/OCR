from app import crud, models, schemas, utils
from app import exceptions as exc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from app.core.celery_app import celery_app


async def calculator_price(db: AsyncSession, *, score, skip, limit, asc):
    records = await crud.record.find_records(
        db, input_score=score, skip=skip, limit=limit, asc=asc
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
        price_weekly_day = weekdays[item_record.end_time.weekday()]
        item_record.parking_time = str(
            item_record.end_time - item_record.start_time
        )
        hours, minutes, seconds = map(int, item_record.parking_time.split(":"))
        total_hours = hours + minutes / 60 + seconds / 3600
        item_record.parking_price = (
            total_hours * item_record.price_model[price_weekly_day]
        )

    return schemas.GetRecords(items=records[0], all_items_count=records[1])
