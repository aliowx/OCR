from fastapi import APIRouter

from .api.plate import router as report_router

router = APIRouter()
router.include_router(report_router, prefix="/plate", tags=["plate(black/white)"])