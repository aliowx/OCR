from sqlalchemy.ext.asyncio import AsyncSession
from app.plate.schemas.plate import ParamsPlate
from app.plate.repo import plate_repo


async def get_multi_plate_by_filter(db: AsyncSession, *, params: ParamsPlate):

    plates, total_count = await plate_repo.get_multi_by_filter(
        db, params=params
    )

    return plates, total_count
