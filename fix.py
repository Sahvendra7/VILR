with open("simulator/attacks.py", "r") as f:
    content = f.read()

# Fix extract_outcome specifically
content = content.replace(
    "return ExecutionResult(AttackOutcome.NOT_BLOCKED, resp.status_code)",
    "return ExecutionResult(AttackOutcome.NOT_BLOCKED, response.status_code)"
)
content = content.replace(
    "return ExecutionResult(AttackOutcome.INCONCLUSIVE, resp.status_code)",
    "return ExecutionResult(AttackOutcome.INCONCLUSIVE, response.status_code)"
)

with open("simulator/attacks.py", "w") as f:
    f.write(content)
