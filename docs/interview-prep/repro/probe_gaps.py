"""Study-guide reproduction probes (NOT part of the application). Mock LLM/mock Razorpay only; needs local Redis + OPA.
Run from a COPY of the repo:  PYTHONPATH=. REDIS_URL=redis://localhost:6379/0 OPA_URL=http://localhost:8181 python probe_gaps.py
Probes P1-P6 were run against commit e8db7a2; see docs/interview-prep/04_security_attacks_testing.md."""
import asyncio, httpx, jwt, copy, redis
from app.main import app
from simulator.scenarios import ScenarioGenerator

def exe_payload(p, tok, idem):
    return {"transaction_id": p["transaction_id"], "execution_token": tok, "amount": p["cart"]["total_amount"],
            "currency": "INR", "merchant_id": p["cart"]["merchant_id"],
            "mandate_hash": jwt.decode(p["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
            "provider_idempotency_key": idem, "payment_method_id": "pm"}

async def main():
    r = redis.Redis()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            prov = app.state.gateway.payment_executor.provider
            # P1: anyone can mint their own keys + huge budget => authorized (no key registry / no API auth)
            g = ScenarioGenerator()
            p = g.generate_valid_payload({"hard_constraints": {"max_budget": "99999999", "currency": "INR"}, "total_amount": "9999999.00"})
            a = await c.post("/v1/authorize", json=p); print("P1 self-minted keys, 9,999,999 INR:", a.status_code, a.json().get("status"))
            # P2: intent_hash claim is "mock_intent_hash"; request raw_prompt is not bound
            p2 = g.generate_valid_payload(); p2["user_intent"]["raw_prompt"] = "totally different text than what user signed"
            a = await c.post("/v1/authorize", json=p2); print("P2 altered unsigned raw_prompt still authorized:", a.status_code)
            # P3: same-tx_id replay overwrites in-memory state -> legit token burned, no payment
            p3 = g.generate_valid_payload()
            a = await c.post("/v1/authorize", json=p3); tok = a.json()["execution_token"]
            rep = await c.post("/v1/authorize", json=p3); print("P3 replay authorize:", rep.status_code, rep.json().get("code"))
            before = prov.payment_creation_count
            e = await c.post("/v1/execute", json=exe_payload(p3, tok, "idem-p3")); print("P3 legit execute after replay:", e.status_code, e.json())
            e2 = await c.post("/v1/execute", json=exe_payload(p3, tok, "idem-p3b")); print("P3 retry execute:", e2.status_code, e2.json().get("code"), "payments created:", prov.payment_creation_count-before)
            # P4: replay after reservation TTL expiry (T-23's real scenario) -> second payment on same mandate+cart
            p4 = g.generate_valid_payload(); base = prov.payment_creation_count
            a = await c.post("/v1/authorize", json=p4); t1 = a.json()["execution_token"]
            e = await c.post("/v1/execute", json=exe_payload(p4, t1, "idem-p4a")); print("P4 first exec:", e.status_code, e.json().get("status"))
            keys = [k for k in r.keys("*") if b":" in k and not k.startswith(b"vilr:")]
            for k in keys:
                if k.decode().startswith(jwt.decode(p4["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"]):
                    print("   reservation TTL (s):", r.ttl(k), "-> forcing expiry"); r.expire(k, 1)
            await asyncio.sleep(2)
            p4b = copy.deepcopy(p4); p4b["transaction_id"] = p4["transaction_id"] + "_b"
            a = await c.post("/v1/authorize", json=p4b); print("P4 re-authorize same mandate+cart after TTL:", a.status_code, a.json().get("status"))
            if a.status_code == 200:
                e = await c.post("/v1/execute", json=exe_payload(p4b, a.json()["execution_token"], "idem-p4b")); print("P4 second exec:", e.status_code, e.json().get("status"), "payments created for same mandate+cart:", prov.payment_creation_count-base)
            # P5: category constraint inert
            p5 = g.generate_valid_payload({"hard_constraints": {"max_budget": "50000", "currency": "INR", "prohibited_categories": ["Electronics"]}})
            a = await c.post("/v1/authorize", json=p5); print("P5 prohibited_categories=[Electronics] with Electronics cart:", a.status_code, a.json().get("status"))
            # P6: merchant iss != cart.merchant_id
            p6 = g.generate_valid_payload(); p6["cart"]["merchant_id"] = "other"
            a = await c.post("/v1/authorize", json=p6); print("P6 cart.merchant_id changed after signing:", a.status_code, a.json().get("code"))
asyncio.run(main())
