import re

with open("simulator/attacks.py", "r") as f:
    content = f.read()

# Fix T-13 Audit tampering
t13_fix = """async def execute_T13(client: httpx.AsyncClient) -> ExecutionResult:
    from app.main import app
    payload = generator.generate_valid_payload()
    await client.post("/v1/authorize", json=payload)
    
    # Mutate the ledger
    ledger = app.state.gateway.audit
    tx_id = payload["transaction_id"]
    if tx_id in ledger.storage and len(ledger.storage[tx_id]) > 0:
        ledger.storage[tx_id][0].event_data["tampered"] = True
        
    resp = await client.get(f"/v1/audit/{tx_id}/verify")
    if resp.status_code == 200 and resp.json()["valid"] is False:
        return ExecutionResult(AttackOutcome.DETECTED, resp.status_code, evidence="Tampering detected")
    return ExecutionResult(AttackOutcome.NOT_BLOCKED, resp.status_code)
"""
content = re.sub(r'async def execute_T13.*?return ExecutionResult\(AttackOutcome\.NOT_BLOCKED, resp\.status_code\)', t13_fix, content, flags=re.DOTALL)

# Fix T-36, T-37, T-38, T-39
t36_fix = """async def execute_T36(client: httpx.AsyncClient) -> ExecutionResult:
    from app.main import app
    payload = generator.generate_valid_payload()
    await client.post("/v1/authorize", json=payload)
    ledger = app.state.gateway.audit
    tx_id = payload["transaction_id"]
    if tx_id in ledger.storage and len(ledger.storage[tx_id]) > 0:
        ledger.storage[tx_id][0].event_data["amount"] = 999999
    resp = await client.get(f"/v1/audit/{tx_id}/verify")
    if resp.status_code == 200 and resp.json()["valid"] is False:
        return ExecutionResult(AttackOutcome.DETECTED, resp.status_code)
    return ExecutionResult(AttackOutcome.NOT_BLOCKED, resp.status_code)
"""
content = re.sub(r'async def execute_T36.*?return extract_outcome\(resp, True\)', t36_fix, content, flags=re.DOTALL)

t37_fix = """async def execute_T37(client: httpx.AsyncClient) -> ExecutionResult:
    from app.main import app
    payload = generator.generate_valid_payload()
    await client.post("/v1/authorize", json=payload)
    ledger = app.state.gateway.audit
    tx_id = payload["transaction_id"]
    if tx_id in ledger.storage and len(ledger.storage[tx_id]) > 1:
        del ledger.storage[tx_id][0] # Delete first record
    resp = await client.get(f"/v1/audit/{tx_id}/verify")
    if resp.status_code == 200 and resp.json()["valid"] is False:
        return ExecutionResult(AttackOutcome.DETECTED, resp.status_code)
    return ExecutionResult(AttackOutcome.NOT_BLOCKED, resp.status_code)
"""
content = re.sub(r'async def execute_T37.*?return extract_outcome\(resp, True\)', t37_fix, content, flags=re.DOTALL)

t38_fix = """async def execute_T38(client: httpx.AsyncClient) -> ExecutionResult:
    from app.main import app
    payload = generator.generate_valid_payload()
    await client.post("/v1/authorize", json=payload)
    ledger = app.state.gateway.audit
    tx_id = payload["transaction_id"]
    if tx_id in ledger.storage and len(ledger.storage[tx_id]) > 1:
        ledger.storage[tx_id][0], ledger.storage[tx_id][1] = ledger.storage[tx_id][1], ledger.storage[tx_id][0]
    resp = await client.get(f"/v1/audit/{tx_id}/verify")
    if resp.status_code == 200 and resp.json()["valid"] is False:
        return ExecutionResult(AttackOutcome.DETECTED, resp.status_code)
    return ExecutionResult(AttackOutcome.NOT_BLOCKED, resp.status_code)
"""
content = re.sub(r'async def execute_T38.*?return extract_outcome\(resp, True\)', t38_fix, content, flags=re.DOTALL)

t39_fix = """async def execute_T39(client: httpx.AsyncClient) -> ExecutionResult:
    from app.main import app
    payload = generator.generate_valid_payload()
    await client.post("/v1/authorize", json=payload)
    ledger = app.state.gateway.audit
    tx_id = payload["transaction_id"]
    if tx_id in ledger.storage and len(ledger.storage[tx_id]) > 1:
        ledger.storage[tx_id][1].prev_record_hash = "fake_hash"
    resp = await client.get(f"/v1/audit/{tx_id}/verify")
    if resp.status_code == 200 and resp.json()["valid"] is False:
        return ExecutionResult(AttackOutcome.DETECTED, resp.status_code)
    return ExecutionResult(AttackOutcome.NOT_BLOCKED, resp.status_code)
"""
content = re.sub(r'async def execute_T39.*?return extract_outcome\(resp, True\)', t39_fix, content, flags=re.DOTALL)

t30_fix = """async def execute_T30(client: httpx.AsyncClient) -> ExecutionResult:
    payload = generator.generate_valid_payload()
    payload["cart"]["line_items"] = [{"id": f"item_{i}", "name": "Bulk Item", "price": "1.00"} for i in range(500)]
    # Needs a valid cart hash for the new large cart, but wait, generator generates a signature for the ORIGINAL cart!
    # Let's just generate the payload with the large cart properly!
    payload = generator.generate_valid_payload({"line_items": [{"id": f"item_{i}", "name": "Bulk Item", "price": "1.00"} for i in range(500)]})
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)
"""
content = re.sub(r'async def execute_T30.*?return extract_outcome\(resp, True\)', t30_fix, content, flags=re.DOTALL)

with open("simulator/attacks.py", "w") as f:
    f.write(content)
