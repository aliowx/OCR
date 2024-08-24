from fastapi import APIRouter

from .api.payment import router as payment_router


router = APIRouter()

router.include_router(payment_router, prefix="/payment", tags=["payment"])
