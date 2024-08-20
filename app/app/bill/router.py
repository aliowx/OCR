from fastapi import APIRouter

from .api.bill import router as bill_router


router = APIRouter()

router.include_router(bill_router, prefix="/bill", tags=["bill"])
