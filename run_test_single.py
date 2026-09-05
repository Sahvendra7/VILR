import asyncio
from httpx import ASGITransport, AsyncClient
from app.main import app
from simulator.scenarios import ScenarioGenerator
import jwt

async def main():
    generator = ScenarioGenerator()
    async with app.router.lifespan_context(app), AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        payload = generator.generate_valid_payload()
        r = await test_client.post("/v1/authorize", json=payload)
        token = r.json()["execution_token"]
        
        exe_payload = {
            "transaction_id": payload["transaction_id"], 
            "execution_token": token,
            "amount": "45000.00",
            "currency": "INR",
            "merchant_id": payload["cart"]["merchant_id"],
            "mandate_hash": jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
            "provider_idempotency_key": "idem",
            "payment_method_id": "pm-123"
        }
        r_exec = await test_client.post("/v1/execute", json=exe_payload)
        print("Status:", r_exec.status_code)
        print("Text:", r_exec.text)

asyncio.run(main())
