from fastapi import APIRouter

from .api.price import router as price_router

router = APIRouter()
router.include_router(price_router, prefix="/price", tags=["price"])
