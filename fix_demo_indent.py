import re
with open("scripts/cli.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "async def mock_opa(" in line or "app.state.gateway" in line or "fake_tokens =" in line or "async def mock_create_token" in line or "async def mock_consume_token" in line or "if token not in fake_tokens" in line or "if fake_tokens[token]" in line or "from app.domain.errors" in line or "raise" in line or "return " in line or "async def mock_reserve" in line or "if 'replay'" in line or "async def mock_commit" in line or "pass" in line:
        pass # We will just rewrite this properly
    new_lines.append(line)

# Let's just sed the whole file
