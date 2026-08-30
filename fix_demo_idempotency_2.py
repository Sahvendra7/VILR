import re
with open("scripts/cli.py", "r") as f:
    content = f.read()

content = content.replace("async def reserve(self, key, tx, ttl):", "async def try_reserve(self, key, tx, ttl):")

with open("scripts/cli.py", "w") as f:
    f.write(content)
