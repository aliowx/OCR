from fastapi import APIRouter

from .api.equipment import router as equipment_router
from .api.parking import router as parking_router
from .api.spot import router as spot_router
from .api.zone import router as zone_router
from .api.rule import router as rule_router

router = APIRouter()
router.include_router(parking_router, prefix="/parking", tags=["parking"])
router.include_router(
    zone_router, prefix="/zone", tags=["zone"]
)
router.include_router(
    spot_router, prefix="/spot", tags=["spot"]
)
router.include_router(
    equipment_router, prefix="/equipment", tags=["equipment"]
)
router.include_router(rule_router, prefix="/rule", tags=["rule"])
