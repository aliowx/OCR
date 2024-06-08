from fastapi import APIRouter

from .api.camera import router as camera_router
from .api.equipment import router as equipment_router
from .api.parking import router as parking_router
from .api.parkinglot import router as parkinglot_router
from .api.parkingzone import router as parkingzone_router

router = APIRouter()
router.include_router(parking_router, prefix="/parking", tags=["parking"])
router.include_router(
    parkingzone_router, prefix="/parkingzone", tags=["parkingzone"]
)
router.include_router(
    parkinglot_router, prefix="/parkinglot", tags=["parkinglot"]
)
router.include_router(camera_router, prefix="/camera", tags=["camera"])
router.include_router(
    equipment_router, prefix="/equipment", tags=["equipment"]
)
