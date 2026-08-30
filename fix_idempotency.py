import re

with open("app/domain/interfaces.py", "r") as f:
    content = f.read()

# Add methods to IdempotencyStore interface
methods = """
    @abstractmethod
    async def create_execution_token(self, token: str, transaction_id: str, auth_data: dict, ttl_seconds: int = 3600) -> None:
        pass

    @abstractmethod
    async def consume_execution_token(self, token: str, transaction_id: str) -> dict:
        pass
"""
if "def create_execution_token" not in content:
    content = content.replace(
        "async def is_reserved_or_committed(self, key: str) -> Tuple[bool, Optional[str]]:\n        pass",
        "async def is_reserved_or_committed(self, key: str) -> Tuple[bool, Optional[str]]:\n        pass\n" + methods
    )

with open("app/domain/interfaces.py", "w") as f:
    f.write(content)

