with open("simulator/attacks.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "async def execute_" in line and "-> AttackOutcome:" in line:
        lines[i] = line.replace("-> AttackOutcome:", "-> ExecutionResult:")
    if "ExecutionResult(AttackOutcome.DETECTED, response.status_code)" in line and "T13" not in line:
        lines[i] = line.replace("response.status_code", "resp.status_code")
    if "ExecutionResult(AttackOutcome.NOT_BLOCKED, response.status_code)" in line and "T13" not in line and "extract_outcome" not in line:
        lines[i] = line.replace("response.status_code", "resp.status_code")
        
with open("simulator/attacks.py", "w") as f:
    f.writelines(lines)
