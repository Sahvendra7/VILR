with open("demo_template.txt", "r") as f:
    text = f.read()

text = text.replace("from app.idempotency.store import FakeIdempotencyStore", """
    class FakeIdempotencyStore:
        async def try_reserve_execution(self, transaction_id, idempotency_key):
            return True
        async def release_execution(self, transaction_id, idempotency_key):
            pass
        async def commit_execution(self, transaction_id, idempotency_key, receipt):
            pass
        async def get_receipt(self, transaction_id, idempotency_key):
            return None
""")

with open("demo_template.txt", "w") as f:
    f.write(text)
