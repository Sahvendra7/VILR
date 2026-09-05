import pytest
import copy
from simulator.scenarios import ScenarioGenerator
from httpx import ASGITransport, AsyncClient
from app.main import app

generator = ScenarioGenerator()

@pytest.mark.asyncio
async def test_cart_tampering_http():
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        payload = generator.generate_valid_payload()

        # 1. Authorize original
        r = await test_client.post("/v1/authorize", json=payload)
        assert r.status_code == 200

        # Tamper with cart
        payload_tampered = copy.deepcopy(payload)
        payload_tampered["cart"]["total_amount"] = 999.0

        r2 = await test_client.post("/v1/authorize", json=payload_tampered)
        assert r2.status_code == 400
        assert r2.json()["error"] == "HashMismatch"

        # Test full substitution
        payload_subst = copy.deepcopy(payload)
        payload_subst["cart"]["merchant_id"] = "different_merchant"
        r3 = await test_client.post("/v1/authorize", json=payload_subst)
        assert r3.status_code == 400
        assert r3.json()["error"] == "HashMismatch"

@pytest.mark.asyncio
async def test_opa_routing_http():
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        payload = generator.generate_valid_payload()
        r = await test_client.post("/v1/authorize", json=payload)
        assert r.status_code == 200
        assert "execution_token" in r.json()

