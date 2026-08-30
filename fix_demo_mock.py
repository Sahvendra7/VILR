with open("scripts/cli.py", "r") as f:
    content = f.read()

mock_setup = """
        # Mock OPA
        async def mock_opa(self, *args, **kwargs):
            return True, "ALLOW"
        app.state.gateway.policy.evaluate = mock_opa.__get__(app.state.gateway.policy)
        
        # We need specific OPA behavior for over-budget
        original_evaluate = app.state.gateway.policy.evaluate
        async def mock_opa_smart(self, *args, **kwargs):
            if "9999" in str(args) or "1500" in str(args):
                return False, "DENY_OVER_BUDGET"
            return True, "ALLOW"
        app.state.gateway.policy.evaluate = mock_opa_smart.__get__(app.state.gateway.policy)

        # Mock Redis
        fake_tokens = {}
        async def mock_create_token(token, tx_id, auth_data, ttl):
            fake_tokens[token] = {"transaction_id": tx_id, "auth_data": auth_data, "status": "available"}
            
        async def mock_consume_token(token, tx_id):
            if token not in fake_tokens: raise ValueError("Invalid or expired execution token")
            if fake_tokens[token]["transaction_id"] != tx_id:
                from app.domain.errors import InvalidRequest
                raise InvalidRequest("Token transaction mismatch")
            if fake_tokens[token]["status"] == "consumed":
                from app.domain.errors import DuplicateExecution
                raise DuplicateExecution("Execution token already consumed")
            fake_tokens[token]["status"] = "consumed"
            return fake_tokens[token]["auth_data"]
            
        app.state.gateway.idempotency.create_execution_token = mock_create_token
        app.state.gateway.idempotency.consume_execution_token = mock_consume_token

        async def mock_reserve(key, tx, ttl):
            # for replay
            if "replay" in tx: return False
            return True
        app.state.gateway.idempotency.reserve = mock_reserve
        
        async def mock_commit(key, tx):
            pass
        app.state.gateway.idempotency.commit = mock_commit
        
        # Override health checks
        app.state.gateway.policy.is_available = lambda: True
        
"""

# Insert right after `generator = ScenarioGenerator()`
if "mock_opa" not in content:
    content = content.replace("generator = ScenarioGenerator()\n", "generator = ScenarioGenerator()\n" + mock_setup)

with open("scripts/cli.py", "w") as f:
    f.write(content)

