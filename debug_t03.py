import asyncio
from app.main import app
import httpx
from simulator.scenarios import ScenarioGenerator

async def run():
    gen = ScenarioGenerator()
    payload = gen.generate_valid_payload()
    payload["cart"]["items"][0]["quantity"] = 100
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        async with app.router.lifespan_context(app):
            resp = await client.post("/v1/authorize", json=payload)
            print(resp.status_code)
            print(resp.json())

if __name__ == "__main__":
    asyncio.run(run())
