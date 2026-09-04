import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

text = text.replace('        from app.domain.interfaces import MandateVerifier, IdempotencyStore, PaymentProvider', '    from app.domain.interfaces import MandateVerifier, IdempotencyStore, PaymentProvider')
text = text.replace('policy=policy', 'policy=None')

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
