with open("tests/integration/test_gateway.py", "r") as f:
    content = f.read()

content = content.replace(
    "from app.domain.models import",
    "from app.domain.models import ClosedCheckoutMandate,"
)

with open("tests/integration/test_gateway.py", "w") as f:
    f.write(content)
