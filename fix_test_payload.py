import re

for fn in ["tests/integration/test_concurrency.py", "simulator/attacks.py"]:
    with open(fn, 'r') as f:
        content = f.read()
    
    if "import jwt" not in content:
        content = "import jwt\n" + content
        
    content = content.replace('payload["closed_checkout_token"]["open_mandate_hash"]', 'jwt.decode(payload["closed_checkout_token"], options={"verify_signature": False})["open_mandate_hash"]')
    
    with open(fn, 'w') as f:
        f.write(content)

