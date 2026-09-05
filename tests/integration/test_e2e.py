import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from simulator.scenarios import ScenarioGenerator
import jwt

generator = ScenarioGenerator()

@pytest.mark.asyncio
async def test_canonical_happy_path():
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        payload = generator.generate_valid_payload()
        
        # 1. Authorize
        resp_intent = await test_client.post("/v1/authorize", json=payload)
        assert resp_intent.status_code == 200, resp_intent.text
        token = resp_intent.json()["execution_token"]
        
        # 2. Execute
        exec_payload = {
            "transaction_id": payload["transaction_id"],
            "execution_token": token,
            "amount": str(payload["cart"]["total_amount"]),
            "currency": payload["cart"]["currency"],
            "merchant_id": payload["cart"]["merchant_id"],
            "mandate_hash": jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
            "provider_idempotency_key": "idem-e2e-happypath",
            "payment_method_id": "pm-123"
        }
        resp_exec = await test_client.post("/v1/execute", json=exec_payload)
        assert resp_exec.status_code == 200, resp_exec.text
        assert resp_exec.json()["status"] == "SUCCESS"
