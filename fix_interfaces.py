import re
with open("app/domain/interfaces.py", "r") as f:
    content = f.read()

new_methods = """    async def is_reserved_or_committed(self, key: str) -> Tuple[bool, Optional[str]]:
        ...

    async def create_execution_token(self, token: str, transaction_id: str, auth_data: dict, ttl_seconds: int = 3600) -> None:
        ...

    async def consume_execution_token(self, token: str, transaction_id: str, expected_amount: float, expected_currency: str, expected_merchant: str, expected_hash: str) -> dict:
        ..."""

content = content.replace("    async def is_reserved_or_committed(self, key: str) -> Tuple[bool, Optional[str]]:\n        ...", new_methods)

with open("app/domain/interfaces.py", "w") as f:
    f.write(content)
