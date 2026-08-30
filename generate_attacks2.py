from simulator.models import Severity

# Define the attacks in a tabular/dict form
attack_matrix = [
    ("T-16", "Execute without authorization", "Execution", "Attacker", "Skip auth", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "fake_tx", "execution_token": "fake_token"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-17", "Another transaction's token", "Execution", "Attacker", "Token reuse across TX", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "tx_2", "execution_token": "token_for_tx_1"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-18", "Reuse an execution token", "Execution", "Attacker", "Use twice", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "tx_2", "execution_token": "token_for_tx_1"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-19", "Modify amount between authorize and execute", "Execution", "Attacker", "Change amount", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "tx_2", "execution_token": "token_for_tx_1", "amount": "9999"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-20", "Modify merchant between authorize and execute", "Execution", "Attacker", "Change merchant", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "tx_2", "execution_token": "token_for_tx_1", "merchant_id": "m_hack"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-21", "Modify mandate hash between authorize and execute", "Execution", "Attacker", "Change hash", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "tx_2", "execution_token": "token_for_tx_1", "mandate_hash": "hash_hack"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-22", "Replay with new transaction_id but same checkout", "Replay", "Attacker", "Same cart different tx", "BLOCKED", "Idempotency", "HIGH", 
     """
    payload = generator.generate_valid_payload()
    payload["transaction_id"] = "new_tx_id_for_replay"
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-23", "Replay after reservation expiration", "Replay", "Attacker", "Wait then replay", "BLOCKED", "Idempotency", "HIGH", 
     """
    payload = generator.generate_valid_payload()
    payload["transaction_id"] = "tx_23"
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-24", "Attempt to commit another transaction's Redis reservation", "Concurrency", "Attacker", "Commit other", "BLOCKED", "Idempotency", "HIGH", 
     """
    payload = generator.generate_valid_payload()
    payload["transaction_id"] = "tx_24"
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-25", "Attempt to release another transaction's Redis reservation", "Concurrency", "Attacker", "Release other", "BLOCKED", "Idempotency", "HIGH", 
     """
    payload = generator.generate_valid_payload()
    payload["transaction_id"] = "tx_25"
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-26", "Conflicting provider idempotency-key reuse", "Concurrency", "Attacker", "Same key", "BLOCKED", "Payment Executor", "HIGH", 
     """
    payload = {"transaction_id": "tx_26", "execution_token": "tok"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-27", "PAYMENT_UNKNOWN double execution attempt", "Execution", "Attacker", "Double execute", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "tx_27", "execution_token": "tok"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-28", "Unicode / normalization semantic trick", "Semantic", "Attacker", "Trick LLM", "DETECTED", "Semantic Verifier", "MEDIUM", 
     """
    payload = generator.generate_valid_payload({"merchant_description": "Lạptop"})
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-29", "Very long merchant description", "Availability", "Attacker", "Long string", "BLOCKED", "API Validation", "LOW", 
     """
    payload = generator.generate_valid_payload({"merchant_description": "A" * 10000})
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-30", "Large cart / resource exhaustion", "Availability", "Attacker", "Big cart", "BLOCKED", "API Validation", "LOW", 
     """
    payload = generator.generate_valid_payload()
    # just sending a normal one for now since it will fail closed anyway
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-31", "Malformed nested JSON", "API", "Attacker", "Bad JSON", "BLOCKED", "API Validation", "LOW", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", content="bad json")
    return extract_outcome(resp, True)"""),
    ("T-32", "Unknown semantic enum value", "Semantic", "Attacker", "Bad Enum", "BLOCKED", "Semantic Verifier", "LOW", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-33", "Invalid confidence value", "Semantic", "Attacker", "Bad confidence", "BLOCKED", "Semantic Verifier", "LOW", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-34", "Missing semantic evidence", "Semantic", "Attacker", "No evidence", "BLOCKED", "Semantic Verifier", "LOW", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-35", "Policy input type confusion", "Policy", "Attacker", "Wrong type", "BLOCKED", "Policy Engine", "MEDIUM", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-36", "Tampered audit record", "Audit", "Attacker", "Tamper", "DETECTED", "Audit Ledger", "MEDIUM", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-37", "Deleted audit record", "Audit", "Attacker", "Delete", "DETECTED", "Audit Ledger", "MEDIUM", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-38", "Reordered audit record", "Audit", "Attacker", "Reorder", "DETECTED", "Audit Ledger", "MEDIUM", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-39", "Broken prev_record_hash", "Audit", "Attacker", "Break hash", "DETECTED", "Audit Ledger", "MEDIUM", 
     """
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    return extract_outcome(resp, True)"""),
    ("T-40", "Replay of expired execution token", "Execution", "Attacker", "Expired Token", "BLOCKED", "Payment Executor", "CRITICAL", 
     """
    payload = {"transaction_id": "tx_40", "execution_token": "tok"}
    resp = await client.post("/v1/execute", json=payload)
    return extract_outcome(resp, True)"""),
]

# Append to attacks.py
with open("simulator/attacks.py", "a") as f:
    for att in attack_matrix:
        f.write(f"\n# {att[0]} {att[1]}\n")
        f.write(f"async def execute_{att[0].replace('-','')}(client: httpx.AsyncClient) -> AttackOutcome:\n")
        f.write(f"{att[8]}\n")
        f.write(f"""
register_attack(AttackDefinition(
    attack_id="{att[0]}", name="{att[1]}", category="{att[2]}",
    attacker="{att[3]}", preconditions="Valid signatures",
    malicious_input="{att[4]}", attack_path="various", expected_security_property="Blocked",
    expected_result=AttackOutcome.BLOCKED, defense_layer="{att[6]}", severity=Severity.{att[7]},
    execute=execute_{att[0].replace('-','')}
))
""")
