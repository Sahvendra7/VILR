import re
with open("tests/integration/test_security_invariant.py", "r") as f:
    text = f.read()

text = text.replace("gateway.audit = type('MockAudit', (), {'record': __import__('unittest').mock.AsyncMock()})()", "from app.idempotency.audit import MemoryAuditLedger\n    gateway.audit = MemoryAuditLedger()")

with open("tests/integration/test_security_invariant.py", "w") as f:
    f.write(text)
