from fastapi import APIRouter

from .api.notifications import router as report_router

router = APIRouter()
router.include_router(report_router, prefix="/notifications", tags=["notifications"])