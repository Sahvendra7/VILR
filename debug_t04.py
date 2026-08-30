import asyncio
from app.main import app
import httpx
from simulator.scenarios import ScenarioGenerator
from simulator.attacks import execute_T04

async def run():
    gen = ScenarioGenerator()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        async with app.router.lifespan_context(app):
            res = await execute_T04(client)
            print(res)

if __name__ == "__main__":
    asyncio.run(run())
