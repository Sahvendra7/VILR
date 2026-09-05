import re
with open('scripts/cli.py', 'r') as f:
    content = f.read()

mock_class = """
class MockPolicyEngine:
    def __init__(self, *args, **kwargs):
        pass
    async def evaluate(self, input_data: dict) -> AuthorizationDecision:
        if input_data.get("semantic_decision") != "PASS":
            return AuthorizationDecision(allowed=False, reason="Semantic validation failed")
        if float(input_data.get("amount", 0)) > float(input_data.get("intent_budget", float('inf'))):
            return AuthorizationDecision(allowed=False, reason="Over budget")
        if input_data.get("merchant_id") == "m_untrusted":
            return AuthorizationDecision(allowed=False, reason="Merchant untrusted")
        return AuthorizationDecision(allowed=True, reason="Allowed by policy")
"""
# Need to replace the whole MockPolicyEngine block
# I'll just rewrite the file up to the end of MockPolicyEngine.
