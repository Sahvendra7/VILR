with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace(
    "policy_version=record.policy_metadata.get(\"version\", \"1.0\") if getattr(record, \"policy_metadata\", None) else \"1.0\",",
    "policy_version=record.explanation.get(\"policy_version\", \"1.0\") if getattr(record, \"explanation\", None) else \"1.0\","
)
with open("app/domain/gateway.py", "w") as f:
    f.write(content)
