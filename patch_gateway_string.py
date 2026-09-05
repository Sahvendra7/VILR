with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace(
    "hash=getattr(decision, \"policy_hash\", \"unknown\")",
    "hash=str(getattr(decision, \"policy_hash\", \"unknown\"))"
)
content = content.replace(
    "version=getattr(decision, \"policy_version\", \"unknown\")",
    "version=str(getattr(decision, \"policy_version\", \"unknown\"))"
)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
