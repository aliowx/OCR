from fastapi import APIRouter

from app.api.endpoints import (
    camera,
    images,
    parking,
    plates,
    price,
    records,
    users,
    utils,
)

api_router = APIRouter()
api_router.include_router(users.router, prefix="/user", tags=["users"])
api_router.include_router(utils.router, prefix="/util", tags=["utils"])
api_router.include_router(parking.router, prefix="/parking", tags=["parking"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(camera.router, prefix="/camera", tags=["camera"])
api_router.include_router(plates.router, prefix="/plates", tags=["plates"])
api_router.include_router(records.router, prefix="/records", tags=["records"])
api_router.include_router(price.router, prefix="/price", tags=["price"])
