with open("scripts/cli.py", "r") as f:
    content = f.read()

mock_opa = """
        class MockDecision:
            def __init__(self, allowed, reason):
                self.allowed = allowed
                self.reason = reason
                self.policy_version = "v1"
                self.policy_hash = "hash123"
"""
import re
content = re.sub(r'class MockDecision:.*?self.reason = reason', mock_opa.strip(), content, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(content)
