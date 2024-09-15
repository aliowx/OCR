from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from datetime import timedelta


async def get_multi_by_filters(
    db: AsyncSession, *, params: schemas.ParamsRecord
):
    records = await crud.record.get_multi_by_filters(db=db, params=params)
    ## ---> records[0]
    #                   --> record[0] ==> records
    #                   --> record[1] ==> time_park
    #                   --> record[2] ==> zone_name

    resualt_record = []
    for record in records[0]:
        record[0].zone_name = record[2]
        record[0].time_park = round(record[1].total_seconds() / 60)
        resualt_record.append(record[0])
    return schemas.GetRecords(items=resualt_record, all_items_count=records[1])
