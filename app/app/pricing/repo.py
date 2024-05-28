import logging

from app.crud.base import CRUDBase

from .models import Price
from .schemas import PriceCreate, PriceUpdate

logger = logging.getLogger(__name__)


class CRUDPrice(CRUDBase[Price, PriceCreate, PriceUpdate]):
    pass


price = CRUDPrice(Price)
