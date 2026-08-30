with open("scripts/cli.py", "r") as f:
    content = f.read()

mock_idem_class = """
        class FakeIdempotencyStore:
            def __init__(self):
                self.tokens = {}
            async def reserve(self, key, tx, ttl):
                if "replay" in tx: return False
                return True
            async def commit(self, key, tx):
                pass
            async def create_execution_token(self, token, tx_id, auth_data, ttl):
                self.tokens[token] = {"transaction_id": tx_id, "auth_data": auth_data, "status": "available"}
            async def consume_execution_token(self, token, tx_id):
                if token not in self.tokens: raise ValueError("Invalid or expired execution token")
                if self.tokens[token]["transaction_id"] != tx_id:
                    from app.domain.errors import InvalidRequest
                    raise InvalidRequest("Token transaction mismatch")
                if self.tokens[token]["status"] == "consumed":
                    from app.domain.errors import DuplicateExecution
                    raise DuplicateExecution("Execution token already consumed")
                self.tokens[token]["status"] = "consumed"
                return self.tokens[token]["auth_data"]

        app.state.gateway.idempotency = FakeIdempotencyStore()
"""

# replace the mock_create_token and mock_consume_token stuff
import re
content = re.sub(r'fake_tokens = \{\}.*?app.state.gateway.idempotency.commit = mock_commit', mock_idem_class.strip(), content, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(content)
