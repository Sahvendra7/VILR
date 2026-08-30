with open("simulator/models.py", "r") as f:
    content = f.read()

if "payment_creation_count: int = 0" not in content:
    content = content.replace("payment_call_count: int = 0", "payment_call_count: int = 0\n    payment_creation_count: int = 0\n    transaction_id: str = \"\"\n    evidence: str = \"\"\n    actual: str = \"\"")
    with open("simulator/models.py", "w") as f:
        f.write(content)
