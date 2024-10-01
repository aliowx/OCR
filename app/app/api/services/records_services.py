from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from datetime import timedelta
from typing import List, Optional
from fastapi import Query


async def get_multi_by_filters(
    db: AsyncSession,
    *,
    params: schemas.ParamsRecord,
    input_status_record: Optional[List[schemas.record.StatusRecord]] = Query(
        None
    ),
):
    records = await crud.record.get_multi_by_filters(
        db=db, params=params, input_status_record=input_status_record
    )
    ## ---> records[0]
    #                   --> record[0] ==> records
    #                   --> record[1] ==> time_park
    #                   --> record[2] ==> zone_name
    #                   --> record[3] ==> camera_entrance
    #                   --> record[4] ==> camera_exit

    resualt_record = set()
    for record in records[0]:
        record[0].zone_name = record[2] if record[2] else None
        record[0].time_park = (
            round(record[1].total_seconds() / 60) if record[1] else 0
        )
        record[0].camera_entrance = record[3] if record[3] else None
        record[0].camera_exit = record[4] if record[4] else None
        resualt_record.add(record[0])
    return schemas.GetRecords(items=resualt_record, all_items_count=records[1])
