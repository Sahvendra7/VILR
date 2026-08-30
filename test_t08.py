import asyncio
import httpx
from simulator.attacks import execute_T08

async def main():
    async with httpx.AsyncClient(base_url='http://localhost:8000') as client:
        res = await execute_T08(client)
        print(res)

asyncio.run(main())
