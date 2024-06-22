from fastapi import APIRouter

from .api.report import router as report_router

router = APIRouter()
router.include_router(report_router, prefix="/report", tags=["report"])
