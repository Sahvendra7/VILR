import asyncio
import httpx
import json

async def run():
    payload = {
        "input": {
            "mandate": {"max_amount": "50000", "currency": "INR", "exp": 1900000000},
            "cart": {"total_amount": "40000", "currency": "INR", "merchant_id": "m456", "category": "Electronics"},
            "semantic": {"status": "PASS", "confidence": 0.9},
            "current_time": 1700000000
        }
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://localhost:8181/v1/data/vilr/authorization/decision", json=payload)
        print(resp.status_code)
        print(resp.json())

if __name__ == "__main__":
    asyncio.run(run())
