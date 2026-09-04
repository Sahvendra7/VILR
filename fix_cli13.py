with open("demo_template.txt", "r") as f:
    text = f.read()

import re

fake_store = """
    class FakeIdempotencyStore:
        async def try_reserve(self, key, transaction_id, ttl_seconds=300):
            return True
        async def commit(self, key, transaction_id):
            pass
        async def release(self, key, transaction_id):
            pass
        async def is_reserved_or_committed(self, key):
            return False, None
        async def create_execution_token(self, token, transaction_id, auth_data, ttl_seconds=3600):
            pass
        async def consume_execution_token(self, token, transaction_id, expected_amount, expected_currency, expected_merchant, expected_hash):
            return {"transaction_id": transaction_id}

    class FakePolicy:
        async def evaluate(self, user_intent, cart, semantic_result):
            from app.domain.models import AuthorizationDecision
            
            # Simple mock evaluation based on budget
            if float(cart.total_amount) > float(user_intent.hard_constraints.max_budget):
                return AuthorizationDecision(allowed=False, violations=[{"type":"budget", "message":"Exceeded budget"}], policy_version="1.0")
            
            if semantic_result.status != "PASS":
                return AuthorizationDecision(allowed=False, violations=[{"type":"semantic", "message":"Semantic mismatch"}], policy_version="1.0")
                
            return AuthorizationDecision(allowed=True, violations=[], policy_version="1.0")
            
        def is_available(self):
            return True

    app.state.gateway.idempotency = FakeIdempotencyStore()
    app.state.gateway.policy = FakePolicy()
"""

# Replace the fake redis instantiation
text = re.sub(r'    import fakeredis\.aioredis.*?(?=        generator = ScenarioGenerator\(\))', fake_store, text, flags=re.DOTALL)

# Since token1 might be None because OPA was failing, the condition `if token1:` was skipping S4.
# Let's ensure token1 gets created by the mock.

with open("demo_template.txt", "w") as f:
    f.write(text)
