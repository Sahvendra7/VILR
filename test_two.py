import asyncio
from simulator.scenarios import ScenarioGenerator
from httpx import ASGITransport, AsyncClient
from app.main import app
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
            "amount": 800.00,
            "currency": "USD",
            "merchant_id": payload["cart"]["merchant_id"],
            "mandate_hash": jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
            "provider_idempotency_key": "idem-unknown",
            "payment_method_id": "pm-123"
        }
        
        # Let's see what is authorized in Redis vs exe_payload
        import json
        import redis.asyncio as redis
        from app.config import settings
        r_client = redis.from_url("redis://localhost:6379/0")
        raw = await r_client.get(f"vilr:exec_token:{token}")
        print("REDIS:", raw)
        print("PAYLOAD:", json.dumps(exe_payload))
        
        r_exec = await test_client.post("/v1/execute", json=exe_payload)
        print("Status:", r_exec.status_code)
        print("Body:", r_exec.text)

asyncio.run(main())
