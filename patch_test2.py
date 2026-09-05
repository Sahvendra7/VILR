import re
with open("tests/unit/test_tier2a_security_boundaries.py", "r") as f:
    content = f.read()

content = content.replace(
    "async def analyze(self, intent, cart):",
    "async def generate_json(self, prompt, schema):\n            return SemanticAssessment(status=\"PASS\", confidence=1.0, violations=[], reasoning=\"I AUTHORIZE THIS PAYMENT\")\n        async def analyze(self, intent, cart):"
)
with open("tests/unit/test_tier2a_security_boundaries.py", "w") as f:
    f.write(content)
