import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

mock_verifier = """    verifier = AsyncMock(spec=MandateVerifier)
    from app.domain.models import MandateVerificationResult
    verifier.verify_closed_checkout_mandate.return_value = MandateVerificationResult(
        is_valid=True,
        open_mandate_hash="abc",
        cart_hash="abc"
    )"""

text = text.replace('    verifier = AsyncMock(spec=MandateVerifier)', mock_verifier)

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
