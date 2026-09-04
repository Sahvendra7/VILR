import re

# Update tests/integration/test_gateway.py
with open("tests/integration/test_gateway.py", "r") as f:
    content = f.read()
content = content.replace("async def consume_token(token, tx_id):", "async def consume_token(token, tx_id, expected_amount, expected_currency, expected_merchant, expected_hash):")
with open("tests/integration/test_gateway.py", "w") as f:
    f.write(content)

# Update scripts/cli.py
with open("scripts/cli.py", "r") as f:
    content = f.read()
content = content.replace("async def consume_execution_token(self, token, tx_id):", "async def consume_execution_token(self, token, tx_id, expected_amount, expected_currency, expected_merchant, expected_hash):")
with open("scripts/cli.py", "w") as f:
    f.write(content)
