from sqlalchemy.ext.asyncio import AsyncSession
from app.plate.schemas.plate import ParamsPlate, PlateCreate
from app.plate.repo import plate_repo
from fastapi import UploadFile
import io
import pandas as pd


async def get_multi_plate_by_filter(db: AsyncSession, *, params: ParamsPlate):

    plates, total_count = await plate_repo.get_multi_by_filter(
        db, params=params
    )

    return plates, total_count


async def create_multi_by_excel(db: AsyncSession, *, file: UploadFile):
    contents = await file.read()
    data = pd.read_excel(io.BytesIO(contents))
    plates = data.to_dict(orient="records")

    if plates is not None:
        # Collect all plate numbers from the file
        list_plate = [str(plate["شماره پلاک"]) for plate in plates]

        # Fetch existing plates from the database
        plates_exist = await plate_repo.get_by_plate(db=db, plate=list_plate)
        existing_plates_set = set(
            plates_exist
        )  # Convert to set for faster lookup

        # Filter out plates that already exist in the database
        new_plates = [
            plate
            for plate in plates
            if str(plate["شماره پلاک"]) not in existing_plates_set
        ]

        # Prepare list_data_plate with only new plates
        list_data_plate = [
            PlateCreate(
                name=str(plate["نام و نام خانوادگی"]) or None,
                plate=str(plate["شماره پلاک"]) or None,
                vehicle_color=str(plate["رنگ خودرو"]) or None,
                vehicle_model=str(plate["نوع خودرو"]) or None,
            )
            for plate in new_plates
        ]

        # Insert new plates into the database
        if list_data_plate:
            created_plates = await plate_repo.create_multi(
                db, objs_in=list_data_plate, commit=True
            )
            return created_plates

    return {"status": "No new plates to add"}
