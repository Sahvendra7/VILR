with open("simulator/attacks.py", "r") as f:
    content = f.read()

content = content.replace(
    "def extract_outcome(response: httpx.Response, expected_fail: bool) -> AttackOutcome:",
    "def extract_outcome(response: httpx.Response, expected_fail: bool) -> ExecutionResult:"
)

content = content.replace(
    "return AttackOutcome.NOT_BLOCKED",
    "return ExecutionResult(AttackOutcome.NOT_BLOCKED, response.status_code)"
)

content = content.replace(
    "return AttackOutcome.INCONCLUSIVE",
    "return ExecutionResult(AttackOutcome.INCONCLUSIVE, response.status_code)"
)

# Replace the block
old_block = """    if response.status_code in [400, 422, 403, 500, 404, 401]:
        return AttackOutcome.BLOCKED"""
new_block = """    if response.status_code in [400, 401, 403, 404, 409, 422]:
        return ExecutionResult(AttackOutcome.BLOCKED, response.status_code)
    if response.status_code == 500:
        return ExecutionResult(AttackOutcome.ERROR, response.status_code, "Internal Server Error")"""

content = content.replace(old_block, new_block)

# For T-13 and others where I explicitly returned AttackOutcome
content = content.replace(
    "return AttackOutcome.DETECTED",
    "return ExecutionResult(AttackOutcome.DETECTED, response.status_code)"
)
# Make sure T-04 and T-08 early returns are fixed
content = content.replace(
    "if r.status_code != 200: return AttackOutcome.ERROR",
    "if r.status_code != 200: return ExecutionResult(AttackOutcome.ERROR, r.status_code, 'Setup failed')"
)

# Add import
content = content.replace(
    "from simulator.models import AttackDefinition, AttackOutcome, Severity",
    "from simulator.models import AttackDefinition, AttackOutcome, Severity, ExecutionResult"
)

with open("simulator/attacks.py", "w") as f:
    f.write(content)
