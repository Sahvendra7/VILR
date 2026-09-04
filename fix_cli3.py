with open("scripts/cli.py", "r") as f:
    text = f.read()

fake_store = """
    class FakeIdempotencyStore:
        async def try_reserve_execution(self, transaction_id, idempotency_key):
            return True
        async def release_execution(self, transaction_id, idempotency_key):
            pass
        async def commit_execution(self, transaction_id, idempotency_key, receipt):
            pass
        async def get_receipt(self, transaction_id, idempotency_key):
            return None
"""

text = text.replace("from app.idempotency.store import FakeIdempotencyStore", fake_store)

with open("scripts/cli.py", "w") as f:
    f.write(text)
