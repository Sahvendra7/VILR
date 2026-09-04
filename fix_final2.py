import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

text = text.replace('violations=["Over budget"]', 'violations=[{"rule": "budget_check", "description": "Over budget"}]')
text = text.replace('violations=["Semantic validation failed"]', 'violations=[{"rule": "semantic_status", "description": "Semantic validation failed"}]')
text = text.replace('llm = MockLLMProvider(responses={"*":', 'llm = MockLLMProvider(responses={"USER INTENT":')

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
