import re
with open("tests/unit/test_tier2b_security_boundaries.py", "r") as f:
    content = f.read()

content = content.replace("from app.domain.models import GatewayExecuteRequest", "from app.domain.gateway import GatewayExecuteRequest")

with open("tests/unit/test_tier2b_security_boundaries.py", "w") as f:
    f.write(content)
