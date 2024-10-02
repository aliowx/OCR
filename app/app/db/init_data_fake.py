import logging

from sqlalchemy.orm import Session
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud
from app import models
from app.core.fake_data import fake_data
from app.db.session import AsyncSessionLocal
from app import schemas
import random
import string
from app.core.celery_app import celery_app
from fastapi.encoders import jsonable_encoder
from cache.redis import redis_client
import rapidjson
from datetime import datetime, timedelta, timezone
import time
import asyncio

from app.bill.services.bill import calculate_price_async
from app.bill.schemas import bill as billSchemas


logger = logging.getLogger(__name__)


async def commit_to_db(db: AsyncSession, data: any, name: str):
    db.add(data)
    await db.commit()
    await db.refresh(data)

    logger.info(f"create {name}")

    return data


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for i in range(length))
    return random_string


async def create_parking(db: AsyncSession):
    parking = await db.execute(select(models.Parking).limit(1))

    if not parking:
        parking = fake_data.PARKING
        await commit_to_db(db, data=parking, name="parking")
    return parking


async def create_equipment(db: AsyncSession):
    # Asynchronous query for entrance equipment
    equipment_entrance = await db.execute(
        select(models.Equipment).where(
            models.Equipment.is_deleted == False,
            models.Equipment.equipment_type == 1,
        )
    )
    # Asynchronous query for exit equipment
    equipment_exit = await db.execute(
        select(models.Equipment).where(
            models.Equipment.is_deleted == False,
            models.Equipment.equipment_type == 2,
        )
    )

    # Extract scalars (the actual records) from the query results
    equipment_entrance = equipment_entrance.scalars().all()
    equipment_exit = equipment_exit.scalars().all()

    # Combine entrance and exit equipment into a single list
    equipment = []
    for entrance, exit in zip(equipment_entrance, equipment_exit):
        equipment.append(entrance.id)
        equipment.append(exit.id)

    return equipment


async def create_image(db: AsyncSession):
    image = await db.execute(select(models.Image).limit(1))
    image = image.scalars().first()
    equipment_ids = await create_equipment(db)

    if not image:
        image = fake_data.IMAGE
        image.camera_id = random.choice(equipment_ids)
        await commit_to_db(db, data=image, name="image")

    return image


async def create_price(db: AsyncSession):
    price = await db.execute(
        select(models.Price).filter(
            models.Price.hourly_fee == 0, models.Price.entrance_fee == 20000
        )
    )
    price = price.scalars().first()
    if not price:
        await commit_to_db(
            db,
            data=models.Price(
                name="first simple price", entrance_fee=20000, hourly_fee=0
            ),
            name="price",
        )

    return price


async def create_zone(db: AsyncSession):
    zones = await db.execute(select(models.Zone))
    zones = zones.scalars().all()

    zone_ids = []
    price = await create_price(db)

    for zone in zones:
        if not zone.price_id:
            zone.price_id = price.id
        zone_ids.append(zone.id)

    if not zones:
        zone = fake_data.ZONE
        zone.price_id = price.id
        return await commit_to_db(db, data=zone, name="zone")

    return zone_ids


async def create_sub_zone(db: AsyncSession):
    sub_zone = await db.execute(
        select(models.Zone).where(
            models.Zone.is_deleted == False,
            models.Zone.name == fake_data.SUB_ZONE.name,
        )
    )
    sub_zone = sub_zone.scalars().first()

    if not sub_zone:
        sub_zone = fake_data.SUB_ZONE
        parent_zone = await create_zone(db)
        sub_zone.parent_id = parent_zone[0]  # Assuming first zone ID is used
        await commit_to_db(db, data=sub_zone, name="sub_zone")

    return sub_zone


async def create_records(db: AsyncSession):
    records_data = [
        fake_data.RECORD1,
        fake_data.RECORD2,
    ]
    zone_ids = await create_zone(db)
    image = await create_image(db)
    latest_id = await latest_id_records(db)
    if latest_id is None:
        last_record = None
        for record in records_data:
            record.id = latest_id + 1
            record.img_exit_id = image.id
            record.img_entrance_id = image.id
            record.zone_id = random.choice(zone_ids)
            db.add(record)
            last_record = record  # Store the last added record
    else:
        last_record = None
        for record in records_data:
            record.img_exit_id = image.id
            record.img_entrance_id = image.id
            record.zone_id = random.choice(zone_ids)
            db.add(record)
            last_record = record  # Store the last added record

    await db.commit()
    await db.execute(
        text("SELECT setval('record_id_seq', (SELECT MAX(id) FROM record));")
    )

    if last_record:  # Refresh only if there's a last record
        await db.refresh(last_record)

    logger.info("create record")
    await create_records_past(db)


list_status_record = [
    schemas.StatusRecord.finished.value,
    schemas.StatusRecord.unfinished.value,
    # schemas.StatusRecord.unknown.value,
]

status_bills = [
    billSchemas.StatusBill.unpaid.value,
    billSchemas.StatusBill.paid.value,
]


async def latest_id_records(db: AsyncSession):
    # Asynchronous query to get the latest record ID
    latest_record_query = (
        select(models.Record).order_by(models.Record.id.desc()).limit(1)
    )
    latest_id_result = await db.execute(latest_record_query)
    latest_id_record = latest_id_result.scalars().first()
    if latest_id_record is None:
        return None
    return latest_id_record.id


async def create_records_past(db: AsyncSession):
    # Await asynchronous calls to create_image and create_zone
    image = await create_image(db)
    zone_ids = await create_zone(db)
    latest_id = await latest_id_records(db)

    for i in range(1, 200):
        time = datetime(
            # year=random.randint(2023, 2024),
            year=2024,
            # month=random.randint(1, 9),
            month=9,
            # day=random.randint(1, 20),
            day=random.randint(1, 30),
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )
        record = models.Record(
            id=latest_id + i,
            plate=f"{random.randint(10,99)}{random.randint(10,70)}{random.randint(100,999)}{random.randint(10,99)}",
            start_time=time,
            end_time=time + timedelta(hours=random.randint(1, 23)),
            img_entrance_id=None,
            img_exit_id=None,
            score=0.01,
            zone_id=random.choice(zone_ids),
            latest_status=schemas.StatusRecord.finished.value,
            created=time,
        )
        record.img_entrance_id = image.id
        record.img_exit_id = image.id

        # Add record to the session
        db.add(record)

        # If the record is finished, create a bill
        if record.latest_status == schemas.StatusRecord.finished:
            bill = models.Bill(
                plate=record.plate,
                start_time=record.start_time,
                end_time=record.end_time,
                issued_by=billSchemas.Issued.exit_camera.value,
                price=await calculate_price_async(
                    db,
                    zone_id=record.zone_id,
                    start_time_in=record.start_time,
                    end_time_in=record.end_time,
                ),
                record_id=record.id,
                zone_id=record.zone_id,
                status=random.choice(status_bills),
            )
            db.add(bill)

        # Publish the record data to Redis
        redis_client.publish(
            "records:1", rapidjson.dumps(jsonable_encoder(record))
        )

        # Use async commit/refresh
        await crud.record._commit_refresh(db=db, db_obj=record, commit=False)
    await db.execute(
        text("SELECT setval('record_id_seq', (SELECT MAX(id) FROM record));")
    )
    # Commit all changes after the loop
    await db.commit()


type_event = [
    schemas.event.TypeEvent.entranceDoor.value,
    schemas.event.TypeEvent.exitDoor.value,
]


async def create_events(db: AsyncSession):
    # Await asynchronous calls to create_image and create_equipment
    image = await create_image(db)
    cameras = await create_equipment(db)
    zone_ids = await create_zone(db)
    events = []

    for _ in range(1, 250):
        time = datetime(
            # year=random.randint(2023, 2024),
            year=2024,
            # month=random.randint(1, 9),
            month=9,
            day=random.randint(1, 30),
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )
        time_now = datetime.now(timezone.utc).replace(tzinfo=None)
        event = models.Event(
            plate=f"{random.randint(10, 99)}{random.randint(10, 70)}{random.randint(100, 999)}{random.randint(10, 99)}",
            record_time=time,
            plate_image_id=image.id,
            lpr_image_id=image.id,
            camera_id=random.choice(cameras),
            zone_id=random.choice(zone_ids),
            type_event=random.choice(type_event),
            created=time_now,
        )
        db.add(event)
    await crud.record._commit_refresh(db=db, db_obj=event, commit=True)
    # events.append(event)
    # await crud.record._commit_refresh(db=db, db_obj=event, commit=False)
    # await db.commit()
    # Sending tasks to Celery asynchronously
    # celery_app.send_task(
    #     "add_events",
    #     args=[jsonable_encoder(event)],
    # )

    # Use asyncio.sleep instead of time.sleep to avoid blocking
    # await asyncio.sleep(3)

    # for one_event in events:
    #     event = models.Event(
    #         plate=one_event.plate,
    #         record_time=one_event.record_time
    #         + timedelta(hours=random.randint(1, 16)),
    #         type_event=random.choice(type_event),
    #         plate_image_id=image.id,
    #         lpr_image_id=image.id,
    #         camera_id=one_event.camera_id,
    #         zone_id=one_event.zone_id,
    #         created=time+timedelta(hours=1)
    #     )
    #     db.add(events)
    #     # Sending tasks to Celery asynchronously
    #     # celery_app.send_task(
    #     #     "add_events",
    #     #     args=[jsonable_encoder(event)],
    #     # )
    #     await crud.record._commit_refresh(db=db, db_obj=event, commit=False)
    # await db.commit()


async def init_db_fake_data(db: AsyncSession) -> None:
    try:
        # await create_parking(db)
        # await create_equipment(db)
        # await create_image(db)
        # await create_zone(db)
        # await create_sub_zone(db)
        await create_records(db)
        # await create_records_past(db)
        await create_events(db)
    except Exception as e:
        logger.error(f"initial data creation error\n{e}")

    finally:
        await db.execute(
            text(
                "SELECT setval('record_id_seq', (SELECT MAX(id) FROM record));"
            )
        )
        await db.close()


if __name__ == "__main__":
    db = AsyncSessionLocal()
    asyncio.run(init_db_fake_data())
