import re
with open("scripts/cli.py", "r") as f:
    content = f.read()

content = content.replace("async def commit(self, key, tx):", "async def commit(self, key, tx):\n                pass\n            async def release(self, key, tx):\n                pass\n            async def reserve(self, key, tx, ttl):")

with open("scripts/cli.py", "w") as f:
    f.write(content)
