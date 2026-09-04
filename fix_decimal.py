import re
with open("app/api/schemas.py", "r") as f:
    content = f.read()

content = content.replace("amount: float", "amount: Decimal")
content = "from decimal import Decimal\n" + content

with open("app/api/schemas.py", "w") as f:
    f.write(content)

with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace("amount: float", "amount: Decimal")
content = content.replace("float(request.cart.total_amount)", "str(request.cart.total_amount)")
content = content.replace("float(request.amount)", "str(request.amount)")
content = "from decimal import Decimal\n" + content

with open("app/domain/gateway.py", "w") as f:
    f.write(content)

with open("app/idempotency/store.py", "r") as f:
    content = f.read()

content = content.replace("expected_amount: float", "expected_amount: str")
content = content.replace("tonumber(ARGV[2])", "ARGV[2]")
content = content.replace("if tonumber(data.auth_data.amount) ~= expected_amount then return \"PARAM_MISMATCH\" end", "if tostring(data.auth_data.amount) ~= expected_amount then return \"PARAM_MISMATCH\" end")

with open("app/idempotency/store.py", "w") as f:
    f.write(content)

with open("app/domain/interfaces.py", "r") as f:
    content = f.read()

content = content.replace("expected_amount: float", "expected_amount: str")

with open("app/domain/interfaces.py", "w") as f:
    f.write(content)
