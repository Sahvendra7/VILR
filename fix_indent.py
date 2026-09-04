import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

text = text.replace('    from app.domain.interfaces import MandateVerifier, IdempotencyStore, PaymentProvider\n    from unittest.mock import AsyncMock\n    verifier = AsyncMock(spec=MandateVerifier)\n    idem = AsyncMock(spec=IdempotencyStore)\n    provider = AsyncMock(spec=PaymentProvider)\n    ', '    from app.domain.interfaces import MandateVerifier, IdempotencyStore, PaymentProvider\n    from unittest.mock import AsyncMock\n    verifier = AsyncMock(spec=MandateVerifier)\n    idem = AsyncMock(spec=IdempotencyStore)\n    provider = AsyncMock(spec=PaymentProvider)\n')

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
