import re
with open("generate_perf.py", "r") as f:
    text = f.read()

text = text.replace("gateway = app.state.gateway", "gateway = app.state.gateway\n        from scripts.cli import FakeIdempotencyStore\n        gateway.idempotency = FakeIdempotencyStore()")
with open("generate_perf.py", "w") as f:
    f.write(text)
