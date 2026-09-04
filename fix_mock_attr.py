import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

replacement = """    verifier = AsyncMock(spec=MandateVerifier)
    class FakeResult:
        is_valid = True
        open_mandate_hash = "abc"
        cart_hash = "abc"
        failure_reason = None
    verifier.verify_closed_checkout_mandate.return_value = FakeResult()"""

text = re.sub(r'    verifier = AsyncMock\(spec=MandateVerifier\).*?cart_hash="abc"\n    \)', replacement, text, flags=re.DOTALL)

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
