with open("demo_template.txt", "r") as f:
    text = f.read()

text = text.replace("IdempotencyStore(fakeredis", "RedisIdempotencyStore(fakeredis")
text = text.replace("from app.idempotency.store import IdempotencyStore", "from app.idempotency.store import RedisIdempotencyStore")

with open("demo_template.txt", "w") as f:
    f.write(text)
