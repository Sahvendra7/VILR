with open("demo_template.txt", "r") as f:
    text = f.read()

import re
# Replace FakeIdempotencyStore class definition with imports and fake redis
replacement = """
    import fakeredis.aioredis
    from app.idempotency.store import IdempotencyStore
"""
text = re.sub(r'    class FakeIdempotencyStore:.*?return None\n', replacement, text, flags=re.DOTALL)

# Replace the instantiation
text = text.replace("app.state.gateway.idempotency = FakeIdempotencyStore()", "app.state.gateway.idempotency = IdempotencyStore(fakeredis.aioredis.FakeRedis())")

with open("demo_template.txt", "w") as f:
    f.write(text)
