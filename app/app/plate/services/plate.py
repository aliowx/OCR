from sqlalchemy.ext.asyncio import AsyncSession
from app.plate.schemas.plate import ParamsPlate, PlateCreate, PlateType
from app.plate.repo import plate_repo
from fastapi import UploadFile
import io
import pandas as pd
from collections import Counter
import re


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
        # Initialize lists for valid modified plates and errors
        list_error = []
        list_plate = []
        valid_plates = []

        for plate in plates:
            original_plate = str(plate["شماره پلاک"])

            # Validate and modify the plate format
            # TODO for other type plate
            if not re.fullmatch(r"[0-9\u0600-\u06FF?]{9}", original_plate):
                list_error.append(original_plate)
                continue  # Skip invalid plates

            # Apply replacements based on plate_alphabet_reverse
            modified_plate = original_plate
            for k, v in plate_alphabet_reverse.items():
                modified_plate = modified_plate.replace(k, v)

            list_plate.append(modified_plate)
            valid_plates.append({**plate, "شماره پلاک": modified_plate})
        print(valid_plates)
        # Count occurrences to identify duplicates
        plate_counts = Counter(list_plate)
        duplicates = {
            plate for plate, count in plate_counts.items() if count > 1
        }
        list_duplicate = list(duplicates)

        # Filter out duplicates from valid plates
        new_plates_in = [
            plate
            for plate in valid_plates
            if str(plate["شماره پلاک"]) not in duplicates
        ]

        # Fetch existing plates from the database
        plates_exist = await plate_repo.get_multi_by_plate(
            db=db,
            plate=[plate["شماره پلاک"] for plate in new_plates_in],
            type_list=type_list,
        )

        # Use a set for fast membership testing of existing plates
        pop_plates = {plate for plate in plates_exist}

        # Filter out existing plates and revalidate modified plates
        new_plates = [
            plate
            for plate in new_plates_in
            if plate["شماره پلاک"] not in pop_plates
        ]

        # Prepare list_data_plate for the database insert
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

        # Insert new plates into the database
        created_plates = []
        if list_data_plate:
            created_plates = await plate_repo.create_multi(
                db, objs_in=list_data_plate, commit=True
            )

    return {
        "new": created_plates,
        "exists": list(pop_plates),
        "duplicates": list(list_duplicate),
        "errors": list_error,
    }
