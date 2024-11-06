from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from typing import List, Optional
from fastapi import Query
from app.parking.repo import zone_repo, equipment_repo
from sqlalchemy.orm import Session
from app.models import Equipment, Zone, Record


async def get_multi_by_filters(
    db: AsyncSession,
    *,
    params: schemas.ParamsRecord,
    input_status_record: Optional[List[schemas.record.StatusRecord]] = Query(
        None
    ),
    input_camera_entrance_id: Optional[list[int]] = Query(None),
    input_camera_exit_id: Optional[list[int]] = Query(None),
):
    records = await crud.record.get_multi_by_filters(
        db=db,
        params=params,
        input_status_record=input_status_record,
        input_camera_entrance_id=input_camera_entrance_id,
        input_camera_exit_id=input_camera_exit_id,
    )
    ## ---> records
    #                   --> record[0] ==> records
    #                   --> record[1] ==> time_park
    #                   --> record[2] ==> zone_name
    #                   --> record[3] ==> camera_entrance
    #                   --> record[4] ==> camera_exit

    resualt_record = []
    for record in records[0]:
        record[0].zone_name = record[2]
        record[0].time_park = round(record[1].total_seconds() / 60)
        record[0].camera_entrance = record[3]
        record[0].camera_exit = record[4]
        resualt_record.append(record[0])
    return schemas.GetRecords(items=resualt_record, all_items_count=records[1])
