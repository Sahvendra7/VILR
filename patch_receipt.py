with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace(
    "policy_version=\"1.0\",",
    "policy_version=record.policy_metadata.get(\"version\", \"1.0\") if getattr(record, \"policy_metadata\", None) else \"1.0\",\n            evidence=record.evidence,\n            explanation=record.explanation,"
)
with open("app/domain/gateway.py", "w") as f:
    f.write(content)
