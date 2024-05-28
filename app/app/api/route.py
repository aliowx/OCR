from fastapi import APIRouter

from app.api.endpoints import images, plates, records, utils
from app.parking.router import router as parking_router
from app.pricing.api import router as pricing_router
from app.users.api import router as users_router


api_router = APIRouter()
api_router.include_router(users_router, prefix="/user", tags=["users"])
api_router.include_router(utils.router, prefix="/util", tags=["utils"])
api_router.include_router(parking_router)
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(plates.router, prefix="/plates", tags=["plates"])
api_router.include_router(records.router, prefix="/records", tags=["records"])
api_router.include_router(pricing_router, prefix="/price", tags=["price"])
