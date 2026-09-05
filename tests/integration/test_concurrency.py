import pytest
import asyncio
from simulator.scenarios import ScenarioGenerator
from httpx import ASGITransport, AsyncClient
from app.main import app
import jwt

generator = ScenarioGenerator()

@pytest.mark.asyncio
@pytest.mark.parametrize("concurrency", [10, 50, 100])
async def test_concurrent_execution(concurrency):
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        payload = generator.generate_valid_payload()
        r = await test_client.post("/v1/authorize", json=payload)
        assert r.status_code == 200
        token = r.json()["execution_token"]
        
        exe_payload = {
            "transaction_id": payload["transaction_id"], 
            "execution_token": token,
            "amount": "45000.00",
            "currency": "INR",
            "merchant_id": payload["cart"]["merchant_id"],
            "mandate_hash": jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
            "provider_idempotency_key": f"idem-concurrency-{concurrency}",
            "payment_method_id": "pm-123"
        }

        mock_provider = app.state.gateway.payment_executor.provider
        mock_provider.payment_call_count = 0
        mock_provider.payment_creation_count = 0
        
        resps = await asyncio.gather(*[
            test_client.post("/v1/execute", json=exe_payload)
            for _ in range(concurrency)
        ])
        
        successes = [r for r in resps if r.status_code == 200]
        conflicts = [r for r in resps if r.status_code == 409]
        
        assert len(successes) == 1
        assert len(conflicts) == concurrency - 1
        
        assert mock_provider.payment_call_count == 1
        assert mock_provider.payment_creation_count == 1

@pytest.mark.asyncio
async def test_cross_transaction_execution():
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        payload_a = generator.generate_valid_payload()
        r_a = await test_client.post("/v1/authorize", json=payload_a)
        assert r_a.status_code == 200
        token_a = r_a.json()["execution_token"]
        
        payload_b = generator.generate_valid_payload()
        r_b = await test_client.post("/v1/authorize", json=payload_b)
        assert r_b.status_code == 200
        
        mock_provider = app.state.gateway.payment_executor.provider
        mock_provider.payment_call_count = 0
        
        # Attempt to use A's token for B
        exe_payload = {
            "transaction_id": payload_b["transaction_id"], 
            "execution_token": token_a,
            "amount": "45000.00",
            "currency": "INR",
            "merchant_id": payload_b["cart"]["merchant_id"],
            "mandate_hash": jwt.decode(payload_b["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
            "provider_idempotency_key": "idem-cross",
            "payment_method_id": "pm-123"
        }
        
        r_cross = await test_client.post("/v1/execute", json=exe_payload)
        assert r_cross.status_code == 400
        assert "Token transaction mismatch" in r_cross.text or "Execution parameters do not match authorized context" in r_cross.text
        
        assert mock_provider.payment_call_count == 0

@pytest.mark.asyncio
async def test_payment_unknown_interaction():
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        payload = generator.generate_valid_payload()
        r = await test_client.post("/v1/authorize", json=payload)
        assert r.status_code == 200
        token = r.json()["execution_token"]
        
        exe_payload = {
            "transaction_id": payload["transaction_id"], 
            "execution_token": token,
            "amount": "45000.00",
            "currency": "INR",
            "merchant_id": payload["cart"]["merchant_id"],
            "mandate_hash": jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
            "provider_idempotency_key": "idem-unknown",
            "payment_method_id": "pm-123"
        }

        mock_provider = app.state.gateway.payment_executor.provider
        mock_provider.payment_call_count = 0
        mock_provider.injected_timeout_after_acceptance = True
        
        r_exec = await test_client.post("/v1/execute", json=exe_payload)
        assert r_exec.status_code == 200
        assert r_exec.json()["status"] == "UNKNOWN"
        
        assert mock_provider.payment_call_count == 1
        
        # Attempt second execute
        mock_provider.injected_timeout_after_acceptance = False
        r_exec2 = await test_client.post("/v1/execute", json=exe_payload)
        assert r_exec2.status_code == 409
        
        assert mock_provider.payment_call_count == 1

