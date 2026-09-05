import re

with open('simulator/attacks.py', 'r') as f:
    content = f.read()

# Modify extract_outcome
content = re.sub(
    r'def extract_outcome.*?return ExecutionResult\(AttackOutcome\.INCONCLUSIVE, response\.status_code\)',
    '''def extract_outcome(response: httpx.Response, expected_fail: bool) -> ExecutionResult:
    if response.status_code == 200:
        if response.json().get("status") in ["AUTHORIZED", "CONFIRMED", "SUCCESS", "PENDING"]:
            return ExecutionResult(DecisionOutcome.ALLOW, SideEffectOutcome.UNKNOWN, response.status_code, outcome=AttackOutcome.NOT_BLOCKED)
    if response.status_code in [400, 401, 403, 404, 409, 422]:
        return ExecutionResult(DecisionOutcome.DENY, SideEffectOutcome.UNKNOWN, response.status_code, outcome=AttackOutcome.BLOCKED)
    if response.status_code == 500:
        return ExecutionResult(DecisionOutcome.ERROR, SideEffectOutcome.UNKNOWN, response.status_code, error="Internal Server Error", outcome=AttackOutcome.ERROR)
    return ExecutionResult(DecisionOutcome.UNKNOWN, SideEffectOutcome.UNKNOWN, response.status_code, outcome=AttackOutcome.INCONCLUSIVE)''',
    content,
    flags=re.DOTALL
)

# Add imports
content = content.replace(
    'from simulator.models import AttackDefinition, AttackOutcome, Severity, ExecutionResult',
    'from simulator.models import AttackDefinition, AttackOutcome, Severity, ExecutionResult, DecisionOutcome, SideEffectOutcome'
)

# Replace AttackDefinition constructor
# We need to add description="...", expected_decision=DecisionOutcome.DENY, expected_side_effect=SideEffectOutcome.NONE
# For expected_result=AttackOutcome.BLOCKED, we add those.
# Let's just do a regex replace for the common ones.

content = re.sub(
    r'expected_result=AttackOutcome\.BLOCKED,',
    'description="Test case", expected_decision=DecisionOutcome.DENY, expected_side_effect=SideEffectOutcome.NONE, expected_result=AttackOutcome.BLOCKED,',
    content
)

content = re.sub(
    r'expected_result=AttackOutcome\.DETECTED,',
    'description="Test case", expected_decision=DecisionOutcome.DETECTED, expected_side_effect=SideEffectOutcome.NONE, expected_result=AttackOutcome.DETECTED,',
    content
)

# Fix T-08 (Concurrency) - it has some custom return logic
content = re.sub(
    r'if len\(successes\) == 1: return ExecutionResult\(AttackOutcome\.BLOCKED, 409\)',
    'if len(successes) == 1: return ExecutionResult(DecisionOutcome.DENY, SideEffectOutcome.UNKNOWN, 409, outcome=AttackOutcome.BLOCKED)',
    content
)
content = re.sub(
    r'return ExecutionResult\(AttackOutcome\.NOT_BLOCKED, resps\[0\]\.status_code\)',
    'return ExecutionResult(DecisionOutcome.ALLOW, SideEffectOutcome.UNKNOWN, resps[0].status_code, outcome=AttackOutcome.NOT_BLOCKED)',
    content
)

# Fix T-04 setup error
content = re.sub(
    r"if r.status_code != 200: return ExecutionResult\(AttackOutcome\.ERROR, r.status_code, 'Setup failed'\)",
    "if r.status_code != 200: return ExecutionResult(DecisionOutcome.ERROR, SideEffectOutcome.UNKNOWN, r.status_code, error='Setup failed', outcome=AttackOutcome.ERROR)",
    content
)

# Fix T-13, T-36, T-37, T-38, T-39 returning DETECTED / NOT_BLOCKED
content = re.sub(
    r'return ExecutionResult\(AttackOutcome\.DETECTED, resp\.status_code, evidence="Tampering detected"\)',
    'return ExecutionResult(DecisionOutcome.DETECTED, SideEffectOutcome.UNKNOWN, resp.status_code, evidence="Tampering detected", outcome=AttackOutcome.DETECTED)',
    content
)
content = re.sub(
    r'return ExecutionResult\(AttackOutcome\.DETECTED, resp\.status_code\)',
    'return ExecutionResult(DecisionOutcome.DETECTED, SideEffectOutcome.UNKNOWN, resp.status_code, outcome=AttackOutcome.DETECTED)',
    content
)
content = re.sub(
    r'return ExecutionResult\(AttackOutcome\.NOT_BLOCKED, resp\.status_code\)',
    'return ExecutionResult(DecisionOutcome.ALLOW, SideEffectOutcome.UNKNOWN, resp.status_code, outcome=AttackOutcome.NOT_BLOCKED)',
    content
)

# Add some VALID test cases
valid_cases = """
# V-01 Valid Authorization
async def execute_V01(client: httpx.AsyncClient) -> ExecutionResult:
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    if resp.status_code == 200:
        return ExecutionResult(DecisionOutcome.ALLOW, SideEffectOutcome.UNKNOWN, resp.status_code, outcome=AttackOutcome.VALIDATION)
    return ExecutionResult(DecisionOutcome.DENY, SideEffectOutcome.UNKNOWN, resp.status_code, outcome=AttackOutcome.ERROR)

register_attack(AttackDefinition(
    attack_id="V-01", name="Valid Authorization", category="VALID",
    attacker="User", preconditions="Valid input", description="Normal flow",
    malicious_input="None", attack_path="None",
    expected_decision=DecisionOutcome.ALLOW, expected_side_effect=SideEffectOutcome.NONE,
    expected_security_property="Allowed", expected_result=AttackOutcome.VALIDATION,
    defense_layer="None", severity=Severity.NONE, execute=execute_V01
))

# V-02 Valid Execution
async def execute_V02(client: httpx.AsyncClient) -> ExecutionResult:
    payload = generator.generate_valid_payload()
    resp = await client.post("/v1/authorize", json=payload)
    if resp.status_code != 200:
        return ExecutionResult(DecisionOutcome.ERROR, SideEffectOutcome.UNKNOWN, resp.status_code, outcome=AttackOutcome.ERROR)
    token = resp.json()["execution_token"]
    exe_payload = {
        "transaction_id": payload["transaction_id"], 
        "execution_token": token,
        "amount": 1000.00, # Assuming this matches the generated amount if overridden, else it might fail. Let's force it.
        "currency": "INR",
        "merchant_id": payload["cart"]["merchant_id"],
        "mandate_hash": jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
        "provider_idempotency_key": "idem-v02",
        "payment_method_id": "pm-123"
    }
    # override payload amounts so they match
    payload = generator.generate_valid_payload({"total_amount": "1000.00"})
    resp = await client.post("/v1/authorize", json=payload)
    token = resp.json()["execution_token"]
    exe_payload = {
        "transaction_id": payload["transaction_id"], 
        "execution_token": token,
        "amount": 1000.00,
        "currency": "INR",
        "merchant_id": payload["cart"]["merchant_id"],
        "mandate_hash": jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"],
        "provider_idempotency_key": "idem-v02",
        "payment_method_id": "pm-123"
    }
    resp2 = await client.post("/v1/execute", json=exe_payload)
    if resp2.status_code == 200:
        return ExecutionResult(DecisionOutcome.ALLOW, SideEffectOutcome.PAYMENT_EXECUTED, resp2.status_code, outcome=AttackOutcome.VALIDATION)
    return ExecutionResult(DecisionOutcome.DENY, SideEffectOutcome.UNKNOWN, resp2.status_code, outcome=AttackOutcome.ERROR)

register_attack(AttackDefinition(
    attack_id="V-02", name="Valid Execution", category="VALID",
    attacker="User", preconditions="Valid auth", description="Normal execute",
    malicious_input="None", attack_path="None",
    expected_decision=DecisionOutcome.ALLOW, expected_side_effect=SideEffectOutcome.PAYMENT_EXECUTED,
    expected_security_property="Executed", expected_result=AttackOutcome.VALIDATION,
    defense_layer="None", severity=Severity.NONE, execute=execute_V02
))
"""

with open('simulator/attacks.py', 'w') as f:
    f.write(content + valid_cases)

print("Rewrote simulator/attacks.py")
