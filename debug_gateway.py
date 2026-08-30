import asyncio
from app.domain.models import UserIntent, HardConstraints, Cart, CartItem, Identifier
from app.domain.gateway import GatewayAuthorizeRequest
from app.main import app
import httpx
import uuid
import time
from decimal import Decimal

async def run():
    now = int(time.time())
    
    # Needs valid JWTs, so we just use the generator
    from simulator.scenarios import ScenarioGenerator
    gen = ScenarioGenerator()
    payload = gen.generate_valid_payload()
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        async with app.router.lifespan_context(app):
            resp = await client.post("/v1/authorize", json=payload)
            print(resp.status_code)
            print(resp.json())

if __name__ == "__main__":
    asyncio.run(run())
