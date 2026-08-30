import re
with open("scripts/cli.py", "r") as f:
    content = f.read()

patch_code = """
import fakeredis.aioredis
import redis.asyncio as redis
import app.main
app.main.redis.from_url = lambda url, **kwargs: fakeredis.aioredis.FakeRedis()
import app.idempotency.store
app.idempotency.store.redis.from_url = lambda url, **kwargs: fakeredis.aioredis.FakeRedis()
"""

# Insert at the top
content = patch_code + content

with open("scripts/cli.py", "w") as f:
    f.write(content)
