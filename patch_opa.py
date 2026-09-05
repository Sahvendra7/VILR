with open("app/policy/engine.py", "r") as f:
    content = f.read()

mock_hash = """
import hashlib
import os

def get_policy_metadata() -> dict:
    path = "policies/authorization.rego"
    if not os.path.exists(path):
        return {"name": "payment_authorization", "version": "unknown", "hash": "unknown"}
    with open(path, "rb") as f:
        content = f.read()
    h = hashlib.sha256(content).hexdigest()
    # Read version from file (e.g. policy_version := "v1")
    version = "unknown"
    for line in content.decode("utf-8").splitlines():
        if "policy_version :=" in line:
            version = line.split(":=")[1].strip().strip('"')
            break
    return {"name": "payment_authorization", "version": version, "hash": h}
"""

content = content.replace("import httpx", "import httpx\n" + mock_hash)

# Now inject it into the engine class and add metadata to AuthorizationDecision
content = content.replace(
    "policy_version=result.get(\"policy_version\", \"unknown\")",
    "policy_version=result.get(\"policy_version\", \"unknown\"),\n                    policy_hash=get_policy_metadata()[\"hash\"]"
)

with open("app/policy/engine.py", "w") as f:
    f.write(content)
