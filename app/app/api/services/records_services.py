from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from typing import List, Optional
from fastapi import Query
from app.parking.repo import zone_repo, equipment_repo
from sqlalchemy.orm import Session


async def get_multi_by_filters(
    db: AsyncSession,
    *,
    params: schemas.ParamsRecord,
    input_status_record: Optional[List[schemas.record.StatusRecord]] = Query(
        None
    ),
):
    records = await crud.record.get_multi_by_filters(
        db=db,
        params=params,
        input_status_record=input_status_record,
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


def set_detail_records(db: Session, record):

    if record is not None:
        camera_entrance = camera_exit = zone_name = None
        if record.camera_entrance_id is not None:
            camera_entrance = equipment_repo.get(
                db=db, id=record.camera_entrance_id
            ).tag
        if record.camera_exit_id is not None:
            camera_exit = equipment_repo.get(
                db=db, id=record.camera_exit_id
            ).tag
        if record.zone_id is not None:
            zone_name = zone_repo.get(db=db, id=record.zone_id).name

        record_detail = schemas.RecordForWS(**record.__dict__)
        record_detail.zone_name = zone_name if zone_name is not None else None
        record_detail.time_park = (
            (record.end_time - record.start_time).total_seconds() / 60
        ) or None
        record_detail.camera_entrance = (
            camera_entrance if camera_entrance is not None else None
        )
        record_detail.camera_exit = (
            camera_exit if camera_exit is not None else None
        )
    return record_detail
