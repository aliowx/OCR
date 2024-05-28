import logging

from app.crud.base import CRUDBase
from app.models.price import Price
from app.schemas.price import PriceCreate, PriceUpdate

logger = logging.getLogger(__name__)


class CRUDPrice(CRUDBase[Price, PriceCreate, PriceUpdate]):
    pass


price = CRUDPrice(Price)
