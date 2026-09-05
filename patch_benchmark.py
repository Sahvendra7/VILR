import re

with open("scripts/cli.py", "r") as f:
    content = f.read()

new_benchmark = """async def run_benchmark(args):
    import time
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from simulator.scenarios import ScenarioGenerator
    import numpy as np

    class FakeIdempotencyStore:
        async def try_reserve(self, key, transaction_id, ttl_seconds=300):
            return True
        async def commit(self, key, transaction_id): pass
        async def release(self, key, transaction_id): pass
        async def is_reserved_or_committed(self, key): return False, None
        async def create_execution_token(self, token, transaction_id, auth_data, ttl_seconds=3600): pass
        async def consume_execution_token(self, token, transaction_id, expected_amount, expected_currency, expected_merchant, expected_hash):
            return {"transaction_id": transaction_id}
        async def issue_execution_token(self, *args, **kwargs): pass

    class FakePolicy:
        async def evaluate(self, input_data):
            from app.domain.models import AuthorizationDecision
            return AuthorizationDecision(allowed=True, violations=[], policy_version="v3")
        def is_available(self):
            return True

    print("Running actual performance benchmark (Mode A: Deterministic mock services)...")
    
    # We will run 50 iterations to get meaningful P50, P95, P99
    iterations = 50
    metrics = {
        "deterministic_authorization": [],
        "crypto_verification": [],
        "cart_verification": [],
        "redis_latency": [],
        "opa_latency": [],
        "evidence_construction": [],
        "risk_latency": [],
        "policy_explanation": [],
        "audit_latency": [],
        "gemini_latency": []
    }
    
    async with app.router.lifespan_context(app):
        from app.semantic.provider import MockLLMProvider
        from app.semantic.verifier import AISemanticVerifier
        
        # Determine AI Mode
        if getattr(args, "llm", "mock") == "gemini":
            from app.semantic.provider import GeminiLLMProvider
            gemini = GeminiLLMProvider()
            app.state.gateway.semantic = AISemanticVerifier(gemini)
            print("Mode C: Real Gemini")
            # If using real Gemini, we will reduce iterations to 10 so we don't blow up rate limits
            iterations = 10
        else:
            mock_provider_llm = MockLLMProvider()
            app.state.gateway.semantic = AISemanticVerifier(mock_provider_llm)
            
        app.state.gateway.idempotency = FakeIdempotencyStore()
        app.state.gateway.policy = FakePolicy()
        
        from app.audit.memory import InMemoryAuditLedger
        app.state.gateway.audit = InMemoryAuditLedger()

        generator = ScenarioGenerator()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for i in range(iterations):
                payload = generator.generate_valid_payload({"raw_prompt": "buy this", "semantic_intent": "purchase", "hard_constraints": {"max_budget": "5000.00", "currency": "INR"}})
                
                await client.post("/v1/authorize", json=payload)
                
                if hasattr(app.state.gateway, "_last_perf"):
                    for k, v in app.state.gateway._last_perf.items():
                        if k in metrics:
                            metrics[k].append(v * 1000) # convert to ms
                            
    print("\\n==================================================")
    print("VILR PERFORMANCE")
    print("==================================================")
    print(f"Environment:\\nMac / Python / Simulated backend\\nIterations: {iterations}")
    print("==================================================")
    
    def print_metric(name, display_name):
        arr = metrics.get(name, [])
        if not arr:
            print(f"\\n{display_name}\\nP50: NOT MEASURED\\nP95: NOT MEASURED\\nP99: NOT MEASURED")
            return
            
        p50 = np.percentile(arr, 50)
        p95 = np.percentile(arr, 95)
        p99 = np.percentile(arr, 99)
        print(f"\\n{display_name}\\nP50: {p50:.2f} ms\\nP95: {p95:.2f} ms\\nP99: {p99:.2f} ms")

    print_metric("deterministic_authorization", "Deterministic Authorization")
    print_metric("crypto_verification", "Crypto")
    print_metric("cart_verification", "Cart")
    print_metric("redis_latency", "Redis")
    print_metric("gemini_latency", "Gemini")
    print_metric("opa_latency", "OPA")
    print_metric("evidence_construction", "Decision Evidence")
    print_metric("risk_latency", "Risk")
    print_metric("policy_explanation", "Policy Explanation")
    print_metric("audit_latency", "Audit")"""

content = re.sub(r'async def run_benchmark\(args\):.*?(?=async def run_demo\(args\):)', new_benchmark + '\n\n', content, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(content)

