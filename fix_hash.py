import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

replacement = """    verifier = AsyncMock(spec=MandateVerifier)
    from app.crypto.jcs import compute_checkout_hash
    generator = ScenarioGenerator()
    payload = generator.generate_valid_payload()
    req = GatewayAuthorizeRequest(**payload)
    
    class FakeResult:
        is_valid = True
        open_mandate_hash = "abc"
        cart_hash = compute_checkout_hash(req.cart)
        failure_reason = None
    verifier.verify_closed_checkout_mandate.return_value = FakeResult()"""

text = re.sub(r'    verifier = AsyncMock\(spec=MandateVerifier\).*?verifier\.verify_closed_checkout_mandate\.return_value = FakeResult\(\)', replacement, text, flags=re.DOTALL)

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
