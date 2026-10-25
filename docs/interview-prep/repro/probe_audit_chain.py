"""Study-guide probe P8 (audit chain blind spots). No Redis/OPA needed. Run from repo root: python docs/interview-prep/repro/probe_audit_chain.py
Shows: (a) tail truncation of a transaction's chain is NOT detected, (b) a swallowed/dropped write leaves a chain that still verifies."""
import asyncio
from app.audit.ledger import MemoryAuditLedger
from app.domain.gateway import GatewayOrchestrator
from app.domain.state_machine import TransactionState as S

async def main():
    led = MemoryAuditLedger()
    gw = GatewayOrchestrator(None, None, None, None, None, led)
    for s in (S.INTENT_RECEIVED, S.AP2_VERIFIED, S.CART_VERIFIED, S.AUTHORIZED):
        await gw._log("tx1", s, user_id="u")
    print("before:", await led.verify_chain("tx1"))
    led._store["tx1"].pop()
    print("tail truncated:", await led.verify_chain("tx1"))

    led2 = MemoryAuditLedger(); gw2 = GatewayOrchestrator(None, None, None, None, None, led2)
    orig, n = led2.record, {"i": 0}
    async def flaky(rec):
        n["i"] += 1
        if n["i"] == 2:
            return  # emulates SupabaseAuditLedger.record swallowing an exception
        await orig(rec)
    led2.record = flaky
    for s in (S.INTENT_RECEIVED, S.AP2_VERIFIED, S.CART_VERIFIED):
        await gw2._log("tx2", s, user_id="u")
    print("dropped middle write:", await led2.verify_chain("tx2"), [r.state for r in led2._store["tx2"]])

asyncio.run(main())
