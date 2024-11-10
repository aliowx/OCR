from fastapi import APIRouter

from .api.api_v1.bill_payment import router as payment_router


router = APIRouter()

router.include_router(payment_router, prefix="/payment", tags=["payment"])
