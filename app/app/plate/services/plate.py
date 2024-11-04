from sqlalchemy.ext.asyncio import AsyncSession
from app.plate.schemas.plate import ParamsPlate, PlateCreate, PlateType
from app.plate.repo import plate_repo
from fastapi import Query, UploadFile
import io
import pandas as pd
from collections import Counter


async def get_multi_plate_by_filter(db: AsyncSession, *, params: ParamsPlate):

    plates, total_count = await plate_repo.get_multi_by_filter(
        db, params=params
    )

    return plates, total_count


async def create_multi_by_excel(
    db: AsyncSession, *, file: UploadFile, type_list: PlateType
):
    contents = await file.read()
    data = pd.read_excel(io.BytesIO(contents))
    plates = data.to_dict(orient="records")

    plate_alphabet = {
        # 10: "الف",
        # 10: "آ",
        10: "ا",
        11: "ب",
        12: "پ",
        13: "ت",
        14: "ث",
        15: "ج",
        16: "چ",
        17: "ح",
        18: "خ",
        19: "د",
        20: "ذ",
        21: "ر",
        22: "ز",
        23: "ژ",
        24: "س",
        25: "ش",
        26: "ص",
        27: "ض",
        28: "ط",
        29: "ظ",
        30: "ع",
        31: "غ",
        32: "ف",
        33: "ق",
        34: "ک",
        35: "گ",
        36: "ل",
        37: "م",
        38: "ن",
        39: "و",
        40: "ه",
        41: "ی",
        42: "معلولین",
        43: "تشریفات",
        44: "A",
        45: "B",
        46: "C",
        47: "D",
        48: "E",
        49: "F",
        50: "G",
        51: "H",
        52: "I",
        53: "J",
        54: "K",
        55: "L",
        56: "M",
        57: "N",
        58: "O",
        59: "P",
        60: "Q",
        61: "R",
        62: "S",
        63: "T",
        64: "U",
        65: "V",
        66: "W",
        67: "X",
        68: "Y",
        69: "Z",
        0: "?",
    }

    plate_alphabet_reverse = {v: f"{k:0>2}" for k, v in plate_alphabet.items()}

    if plates is not None:
        # Collect and modify all plate numbers from the file
        list_plate = []
        for plate in plates:
            modified_plate = str(plate["شماره پلاک"])
            for k, v in plate_alphabet_reverse.items():
                modified_plate = modified_plate.replace(k, v)
            list_plate.append(modified_plate)

        # Update plates with the modified list of plate numbers
        for i, plate in enumerate(plates):
            plate["شماره پلاک"] = list_plate[i]

        # Count occurrences of each modified plate number
        plate_counts = Counter(list_plate)

        # Find and store duplicate plates
        duplicates = {
            plate for plate, count in plate_counts.items() if count > 1
        }

        list_duplicate = list(duplicates)

        new_plates_in = [
            plate for plate in plates if plate["شماره پلاک"] not in duplicates
        ]

        # Fetch existing plates from the database
        plates_exist = await plate_repo.get_multi_by_plate(
            db=db,
            plate=[plate["شماره پلاک"] for plate in new_plates_in],
            type_list=type_list,
        )

        # Convert plates_exist to a set of plate numbers for faster lookup
        pop_plates = set(plates_exist)

        # Filter out plates that already exist in the database by comparing only the plate numbers
        new_plates = [
            plate
            for plate in new_plates_in
            if plate["شماره پلاک"] not in pop_plates
        ]

        # Prepare list_data_plate with only new plates
        list_data_plate = [
            PlateCreate(
                name=str(plate["نام و نام خانوادگی"]),
                plate=str(plate["شماره پلاک"]),
                vehicle_color=str(plate["رنگ خودرو"]),
                vehicle_model=str(plate["نوع خودرو"]),
                type=type_list,
                phone_number=(
                    str(plate["تلفن همراه"])
                    if type_list == PlateType.phone
                    else None
                ),
            )
            for plate in new_plates
        ]
        created_plates = []
        # Insert new plates into the database
        if list_data_plate:
            created_plates = await plate_repo.create_multi(
                db, objs_in=list_data_plate, commit=True
            )

    return [
        {
            "new": created_plates,
            "exists": pop_plates,
            "duplicates": list(list_duplicate),
        }
    ]
