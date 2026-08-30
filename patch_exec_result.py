with open("simulator/models.py", "r") as f:
    content = f.read()

if "payment_call_count: int = 0" not in content.split("class ExecutionResult:")[1].split("class AttackDefinition:")[0]:
    content = content.replace("error: str = \"\"", "error: str = \"\"\n    payment_call_count: int = 0\n    payment_creation_count: int = 0\n    transaction_id: str = \"\"\n    evidence: str = \"\"")
    with open("simulator/models.py", "w") as f:
        f.write(content)
