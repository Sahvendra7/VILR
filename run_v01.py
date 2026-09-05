import asyncio
from simulator.attacks import ATTACKS
from app.main import app
import httpx

async def main():
    v1 = [a for a in ATTACKS if a.attack_id == "V-01"][0]
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await v1.execute(client)
        print("HTTP Status:", res.http_status)
        print("Decision:", res.actual_decision)
        print("Outcome:", res.outcome)

asyncio.run(main())
