"""Study-guide probe P7 (open/closed mandate binding, replay-key bypass). Same run conditions as probe_gaps.py."""
import asyncio, httpx, copy, uuid
from app.main import app
from simulator.scenarios import ScenarioGenerator
async def main():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            g = ScenarioGenerator()
            a = g.generate_valid_payload({"closed_mandate_override": {"open_mandate_hash": "GARBAGE-NOT-A-HASH-OF-ANY-OPEN-MANDATE"}})
            r = await c.post("/v1/authorize", json=a); print("P7a closed mandate pointing at nonexistent open mandate:", r.status_code, r.json().get("status"))
            # same user open token + same cart, merchant re-signs with a different bogus open_mandate_hash => different Redis key
            b = g.generate_valid_payload({"closed_mandate_override": {"open_mandate_hash": "GARBAGE-2"}})
            b2 = copy.deepcopy(a); b2["transaction_id"] = "tx_" + uuid.uuid4().hex
            b2["closed_checkout_token"] = g.merchant_signer.sign({**__import__('jwt').decode(a["closed_checkout_token"], options={"verify_signature": False}), "open_mandate_hash":"GARBAGE-3", "mandate_id":"m_closed_x"})
            r1 = await c.post("/v1/authorize", json=a | {"transaction_id":"tx_"+uuid.uuid4().hex}); print("P7b same mandate+cart, same closed hash (replay inside TTL):", r1.status_code, r1.json().get("code"))
            r2 = await c.post("/v1/authorize", json=b2); print("P7c same user mandate+cart, merchant re-signs with different open_mandate_hash:", r2.status_code, r2.json().get("status"))
asyncio.run(main())
