import re

with open("simulator/runner.py", "r") as f:
    content = f.read()

# Replace the second 'payment_creation_count=creations,'
content = re.sub(r'error=str\(e\),\n\s*payment_creation_count=creations,', 'error=str(e),', content)

with open("simulator/runner.py", "w") as f:
    f.write(content)
