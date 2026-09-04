import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

text = text.replace('from app.crypto.jcs import compute_checkout_hash', 'from app.security.crypto import compute_checkout_hash')

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
