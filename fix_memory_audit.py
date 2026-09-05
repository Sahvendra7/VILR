with open("scripts/cli.py", "r") as f:
    content = f.read()

content = content.replace("InMemoryAuditLedger", "MemoryAuditLedger")

with open("scripts/cli.py", "w") as f:
    f.write(content)
