from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from typing import List, Optional
from app.models.base import plate_alphabet_reverse
from app.utils import generate_excel
from datetime import datetime
from app import crud, utils
from app.core import exceptions as exc


async def get_multi_by_filters(
    db: AsyncSession,
    *,
    params: schemas.ParamsRecord,
    input_status_record: Optional[List[schemas.record.StatusRecord]] = None,
    input_camera_entrance_id: Optional[list[int]] = None,
    input_camera_exit_id: Optional[list[int]] = None,
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


async def get_events_by_record_id(db: AsyncSession, *, record_id: int):
    events = await crud.record.get_events_by_record_id(db, record_id=record_id)
    ## ---> event
    #                   --> event[0] ==> events
    #                   --> event[1] ==> camera_name
    #                   --> event[2] ==> zone_name

    resualt_events = []
    for event in events[0]:
        event[0].camera_name = event[1]
        event[0].zone_name = event[2]
        resualt_events.append(event[0])

    return resualt_events, events[1]


async def gen_excel_record(
    db: AsyncSession,
    *,
    params: schemas.ParamsRecord,
    input_status_record: Optional[List[schemas.record.StatusRecord]] = None,
    input_camera_entrance_id: Optional[list[int]] = None,
    input_camera_exit_id: Optional[list[int]] = None,
    input_excel_name: str = f"{datetime.now().date()}",
):
    records = (
        await get_multi_by_filters(
            db,
            params=params,
            input_camera_exit_id=input_camera_exit_id,
            input_camera_entrance_id=input_camera_entrance_id,
            input_status_record=input_status_record,
        )
    ).items
    excel_record = []
    for record in records:
        modified_plate = record.plate
        for k, v in plate_alphabet_reverse.items():
            modified_plate = (
                modified_plate[:2]
                + modified_plate[2:4].replace(v, k)
                + modified_plate[4:]
            )
        fa_alfabet = record.latest_status
        match fa_alfabet:
            case schemas.record.StatusRecord.finished:
                fa_alfabet = "خارج شده"
            case schemas.record.StatusRecord.unfinished:
                fa_alfabet = "در پارکینگ"
            case schemas.record.StatusRecord.unknown:
                fa_alfabet = "نامشخص"
        excel_record.append(
            schemas.record.RecordExcelItem(
                plate=modified_plate,
                start_date=str(record.start_time.date()),
                start_time=str(record.start_time.time()),
                end_date=str(record.end_time.date()),
                end_time=str(record.end_time.time()),
                time_park=record.time_park,
                camera_entrance=record.camera_entrance,
                camera_exit=record.camera_exit,
                latest_status=fa_alfabet,
                zone_name=record.zone_name,
            )
        )
    if excel_record is not None:
        file = generate_excel.get_excel_file_response(
            data=excel_record, title=input_excel_name
        )
        return file
    return {"data": "not exist"}


async def gen_excel_record_for_police(
    db: AsyncSession,
    *,
    params: schemas.ParamsRecord,
    input_status_record: Optional[List[schemas.record.StatusRecord]] = None,
    input_camera_entrance_id: Optional[list[int]] = None,
    input_camera_exit_id: Optional[list[int]] = None,
    input_excel_name: str = f"{datetime.now().date()}",
):
    records = (
        await get_multi_by_filters(
            db,
            params=params,
            input_camera_exit_id=input_camera_exit_id,
            input_camera_entrance_id=input_camera_entrance_id,
            input_status_record=input_status_record,
        )
    ).items
    list_plate = {record.plate for record in records}
    excel_record = []
    for plate in list_plate:
        modified_plate = plate
        for k, v in plate_alphabet_reverse.items():
            modified_plate = (
                modified_plate[:2]
                + modified_plate[2:4].replace(v, k)
                + modified_plate[4:]
            )
        excel_record.append(
            schemas.record.RecordExcelItemForPolice(
                seri=modified_plate[:2],
                hrf=modified_plate[2:3],
                serial=modified_plate[3:6],
                iran=modified_plate[6:8],
            )
        )
    if excel_record is not None:
        file = generate_excel.get_excel_file_response(
            data=excel_record, title=input_excel_name
        )
        return file
    return {"data": "not exist"}


async def update_record_and_events(
    db: AsyncSession,
    *,
    record_id: int,
    params_in: schemas.RecordUpdatePlate,
):
    record = await crud.record.get(db=db, id=record_id)
    if not record:
        exc.ServiceFailure(
            detail="Record Not Found", msg_code=utils.MessageCodes.not_found
        )
    events = await crud.record.all_events_with_one_record_id(
        db, record_id=record.id
    )
    list_events_to_update = []
    for event in events:
        event.plate = params_in.plate
        list_events_to_update.append(event)
    update_multi_events = await crud.event.update_multi(
        db, db_objs=list_events_to_update
    )

    record.end_time = params_in.end_time
    record.latest_status = params_in.latest_status
    update_record = await crud.record.update(db, db_obj=record)

    return update_record
