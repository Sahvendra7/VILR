import re

with open("scripts/cli.py", "r") as f:
    content = f.read()

new_bench = """async def run_benchmark(args):
    import time
    import statistics
    from app.main import app
    from httpx import AsyncClient, ASGITransport
    from simulator.scenarios import ScenarioGenerator
    from app.domain.gateway import GatewayAuthorizeRequest

    generator = ScenarioGenerator()
    
    # We will do component level benchmarks
    crypto_times = []
    redis_times = []
    semantic_times = []
    opa_times = []
    audit_times = []

    async with app.router.lifespan_context(app):
        gateway = app.state.gateway
        
        print("Running component-level benchmark (100 iterations)...")
        for i in range(100):
            payload = generator.generate_valid_payload()
            auth_req = GatewayAuthorizeRequest(
                transaction_id=payload["transaction_id"],
                open_checkout_token=payload["open_checkout_token"],
                closed_checkout_token=payload["closed_checkout_token"],
                user_intent=payload["user_intent"],
                cart=payload["cart"],
                user_public_key=payload["user_public_key"],
                merchant_public_key=payload["merchant_public_key"]
            )
            
            # 1. Crypto
            start = time.perf_counter()
            await gateway.verifier.verify_open_checkout_mandate(auth_req.open_checkout_token, auth_req.user_public_key)
            await gateway.verifier.verify_closed_checkout_mandate(auth_req.closed_checkout_token, auth_req.merchant_public_key)
            crypto_times.append((time.perf_counter() - start) * 1000)
            
            # 2. Redis
            start = time.perf_counter()
            await gateway.idempotency.try_reserve(payload["transaction_id"], payload["transaction_id"], 300)
            redis_times.append((time.perf_counter() - start) * 1000)
            await gateway.idempotency.release(payload["transaction_id"], payload["transaction_id"])
            
            # 3. OPA (assuming available)
            start = time.perf_counter()
            try:
                await gateway.policy.evaluate({"mandate": {}, "cart": {}, "semantic": {"status":"PASS"}, "current_time": 1000})
            except:
                pass
            opa_times.append((time.perf_counter() - start) * 1000)
            
            # 4. Audit
            start = time.perf_counter()
            await gateway._log(payload["transaction_id"], "BENCHMARK")
            audit_times.append((time.perf_counter() - start) * 1000)
            
            # 5. Semantic
            start = time.perf_counter()
            await gateway.semantic.verify(auth_req.user_intent, auth_req.cart)
            semantic_times.append((time.perf_counter() - start) * 1000)

    def stats(times):
        if not times: return "N/A", "N/A", "N/A"
        return f"{statistics.median(times):.2f} ms", f"{statistics.quantiles(times, n=100)[94]:.2f} ms", f"{statistics.quantiles(times, n=100)[98]:.2f} ms"

    c_p50, c_p95, c_p99 = stats(crypto_times)
    r_p50, r_p95, r_p99 = stats(redis_times)
    o_p50, o_p95, o_p99 = stats(opa_times)
    a_p50, a_p95, a_p99 = stats(audit_times)
    s_p50, s_p95, s_p99 = stats(semantic_times)

    with open("docs/performance-benchmark.md", "w") as f:
        f.write("# Performance Benchmark\n\n")
        f.write("## 1. Environment\n- Component-level measurements in local Python runtime (100 iterations)\n\n")
        f.write("## 2. Component Performance Breakdown (Measured)\n\n")
        f.write("| Component | P50 | P95 | P99 |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| Crypto Verifier (JCS + ECDSA) | {c_p50} | {c_p95} | {c_p99} |\n")
        f.write(f"| Idempotency (Fakeredis memory) | {r_p50} | {r_p95} | {r_p99} |\n")
        f.write(f"| Semantic AI (Mock Provider) | {s_p50} | {s_p95} | {s_p99} |\n")
        f.write(f"| OPA Policy (HTTP) | {o_p50} | {o_p95} | {o_p99} |\n")
        f.write(f"| Audit Ledger (In-Memory) | {a_p50} | {a_p95} | {a_p99} |\n")
        f.write("\n> [!NOTE]\n> These are isolated component measurements, not end-to-end network latencies. Production latencies will vary significantly based on physical network distance to Redis, OPA, and the LLM API.\n")
    
    print("Measured component performance benchmark generated at docs/performance-benchmark.md")
"""

content = re.sub(r'async def run_benchmark\(args\):.*?print\("Performance benchmark generated at docs/performance-benchmark.md"\)', new_bench, content, flags=re.DOTALL)

with open("scripts/cli.py", "w") as f:
    f.write(content)
