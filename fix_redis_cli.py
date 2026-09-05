import re
with open('scripts/cli.py', 'r') as f:
    content = f.read()

mock_class = """
class MockIdempotencyStore:
    def __init__(self, *args, **kwargs):
        self.reservations = {}
        self.tokens = {}

    async def try_reserve(self, key: str, transaction_id: str, ttl_seconds: int = 300) -> bool:
        if key in self.reservations and self.reservations[key] != transaction_id:
            return False
        self.reservations[key] = transaction_id
        return True

    async def commit(self, key: str, transaction_id: str) -> None:
        pass

    async def release(self, key: str, transaction_id: str) -> None:
        if self.reservations.get(key) == transaction_id:
            del self.reservations[key]

    async def is_reserved_or_committed(self, key: str) -> bool:
        return key in self.reservations

    async def create_execution_token(self, token: str, transaction_id: str, auth_data: dict, ttl_seconds: int = 300) -> None:
        self.tokens[token] = {
            "transaction_id": transaction_id,
            "amount": str(auth_data.get("amount")),
            "currency": auth_data.get("currency"),
            "merchant": auth_data.get("merchant_id"),
            "hash": auth_data.get("mandate_hash"),
            "consumed": False
        }

    async def consume_execution_token(self, token: str, transaction_id: str, expected_amount: str, expected_currency: str, expected_merchant: str, expected_hash: str) -> dict:
        if token not in self.tokens:
            raise ValueError("Invalid or expired execution token")
        t = self.tokens[token]
        if t["consumed"]:
            raise ValueError("Token already consumed (Replay)")
        if t["transaction_id"] != transaction_id:
            raise ValueError("Ownership failure")
        if t["amount"] != str(expected_amount) or t["currency"] != expected_currency or t["merchant"] != expected_merchant or t["hash"] != expected_hash:
            raise ValueError("Tampering detected")
        t["consumed"] = True
        return t
"""

content = re.sub(r'class MockIdempotencyStore:.*?(?=from app.domain.models)', mock_class, content, flags=re.DOTALL)

with open('scripts/cli.py', 'w') as f:
    f.write(content)
