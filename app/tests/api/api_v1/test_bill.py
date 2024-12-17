import pytest
from httpx import AsyncClient, ASGITransport
from app.core.config import settings
from app.main import app
from tests.utils.utils import random_lower_string
from app.bill.schemas import BillCreate

transport = ASGITransport(app=app)
client = AsyncClient(transport=transport, base_url="http://test")



@pytest.mark.asyncio
class TestBill:
    async def test_bill_create(
        self,
        create_zone: dict,
        create_record: dict,
        create_bill: dict
    ):

        assert "id" in create_bill
        assert "record_id" in create_bill
        assert "zone_id" in create_bill

        assert create_bill["record_id"] == create_record["id"]
        assert create_bill["zone_id"] == create_zone["id"]
