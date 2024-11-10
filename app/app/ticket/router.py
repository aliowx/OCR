from fastapi import APIRouter

from .api.ticket import router as report_router

router = APIRouter()
router.include_router(report_router, prefix="/ticket", tags=["ticket"])