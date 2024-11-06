from fastapi import APIRouter

from .api.excel import router as report_router

router = APIRouter()
router.include_router(report_router, prefix="/excel", tags=["excel"])
