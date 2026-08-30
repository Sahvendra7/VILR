import asyncio
import httpx
from app.main import app
from simulator.scenarios import ScenarioGenerator
import json

async def run():
    generator = ScenarioGenerator()
    payload = generator.generate_valid_payload()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        async with app.router.lifespan_context(app):
            r = await client.post("/v1/authorize", json=payload)
            print(r.status_code, r.text)

if __name__ == "__main__":
    asyncio.run(run())
