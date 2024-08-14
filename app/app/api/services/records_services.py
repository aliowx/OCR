from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from datetime import timedelta


async def calculator_time(db: AsyncSession, *, params: schemas.ParamsRecord):
    records = await crud.record.find_records(
        db=db,
        input_status_record=params.input_status_record,
        input_score=params.input_score,
        input_plate=params.input_plate,
        input_start_create_time=params.input_start_time,
        input_end_create_time=params.input_end_time,
        skip=params.skip,
        limit=params.limit,
        asc=params.asc,
    )

    for record in range(len(records[0])):
        item_record = records[0][record]

        hours, minutes, seconds = map(
            float,
            str(item_record.end_time - item_record.start_time).split(":"),
        )

        item_record.total_time = str(
            timedelta(
                hours=hours,
                minutes=minutes,
                seconds=seconds,
            )
        )
    return schemas.GetRecords(items=records[0], all_items_count=records[1])
