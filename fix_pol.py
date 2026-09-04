import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

text = text.replace('from app.domain.models import AuthorizationDecision, PolicyViolation', 'from app.domain.models import AuthorizationDecision')
text = text.replace('violations=[PolicyViolation(rule="budget_check", description="Over budget")]', 'violations=["Over budget"]')
text = text.replace('violations=[PolicyViolation(rule="semantic_status", description="Semantic validation failed")]', 'violations=["Semantic validation failed"]')


with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
