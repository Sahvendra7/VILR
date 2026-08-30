with open("scripts/cli.py", "r") as f:
    content = f.read()

# Fix OPA mock return type
mock_opa = """
        class MockDecision:
            def __init__(self, allowed, reason):
                self.allowed = allowed
                self.reason = reason
        async def mock_opa(self, *args, **kwargs):
            if "9999" in str(args) or "1500" in str(args):
                return MockDecision(False, "DENY_OVER_BUDGET")
            return MockDecision(True, "ALLOW")
"""
import re
content = re.sub(r'async def mock_opa.*?return True, "ALLOW"', mock_opa.strip(), content, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(content)
