from typing import Awaitable
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud.base import CRUDBase
from app.models.price import Price
from app.schemas.price import PriceCreate, PriceUpdate
import logging

logger = logging.getLogger(__name__)


class CRUDPrice(CRUDBase[Price, PriceCreate, PriceUpdate]):
    pass


price = CRUDPrice(Price)
