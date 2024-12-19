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
        self, create_zone: dict, create_record: dict, create_bill: dict
    ):

        assert "id" in create_bill
        assert "record_id" in create_bill
        assert "zone_id" in create_bill

        assert create_bill["record_id"] == create_record["id"]
        assert create_bill["zone_id"] == create_zone["id"]


    async def test_bill_retrieve(
        self, create_bill: dict  
    ):
        response = await client.get(f"{create_bill['id']}/")
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == create_bill['id']
        assert data['record_id'] == create_bill['record_id']
        assert data['zone_id'] == create_bill['zone_id']
        
        
    async def test_bill_update(
        self, create_zone: dict, create_record: dict, create_bill: dict
    ):
        update_data =  {"zone_id": create_zone["id"], "record_id": create_record["id"]}
        
        response = await client.put(
            f"{create_bill['id']}/update_bills",
            json=update_data
        )
        
        assert response.status_code == 200
        updated_bill = response.json()
        
        
        assert updated_bill['id'] == create_bill['id']
        assert updated_bill['zone_id'] == create_zone['id']
        assert updated_bill['record_id'] == create_record['id']
        
    
