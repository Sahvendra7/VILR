import re
with open("scripts/cli.py", "r") as f:
    text = f.read()

new_func = """async def run_benchmark(args):
    import time, statistics
    from app.main import app
    from httpx import AsyncClient, ASGITransport
    from simulator.scenarios import ScenarioGenerator
    from app.domain.gateway import GatewayAuthorizeRequest

    generator = ScenarioGenerator()
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
            
            start = time.perf_counter()
            await gateway.verifier.verify_open_checkout_mandate(auth_req.open_checkout_token, auth_req.user_public_key)
            await gateway.verifier.verify_closed_checkout_mandate(auth_req.closed_checkout_token, auth_req.merchant_public_key)
            crypto_times.append((time.perf_counter() - start) * 1000)
            
            start = time.perf_counter()
            await gateway.idempotency.try_reserve(payload["transaction_id"], payload["transaction_id"], 300)
            redis_times.append((time.perf_counter() - start) * 1000)
            await gateway.idempotency.release(payload["transaction_id"], payload["transaction_id"])
            
            start = time.perf_counter()
            try:
                await gateway.policy.evaluate({"mandate": {}, "cart": {}, "semantic": {"status":"PASS"}, "current_time": 1000})
            except:
                pass
            opa_times.append((time.perf_counter() - start) * 1000)
            
            start = time.perf_counter()
            await gateway._log(payload["transaction_id"], "BENCHMARK")
            audit_times.append((time.perf_counter() - start) * 1000)
            
            start = time.perf_counter()
            await gateway.semantic.verify(auth_req.user_intent, auth_req.cart)
            semantic_times.append((time.perf_counter() - start) * 1000)

    def stats(times):
        if not times: return "N/A", "N/A", "N/A"
        return f"{statistics.median(times):.2f} ms", f"{statistics.quantiles(times, n=100)[94]:.2f} ms", f"{statistics.quantiles(times, n=100)[98]:.2f} ms"

    c = stats(crypto_times)
    r = stats(redis_times)
    o = stats(opa_times)
    a = stats(audit_times)
    s = stats(semantic_times)

    lines = [
        "# Performance Benchmark\\n\\n",
        "## 1. Environment\\n- Component-level measurements in local Python runtime (100 iterations)\\n\\n",
        "## 2. Component Performance Breakdown (Measured)\\n\\n",
        "| Component | P50 | P95 | P99 |\\n",
        "|---|---|---|---|\\n",
        f"| Crypto Verifier (JCS + ECDSA) | {c[0]} | {c[1]} | {c[2]} |\\n",
        f"| Idempotency (Fakeredis memory) | {r[0]} | {r[1]} | {r[2]} |\\n",
        f"| Semantic AI (Mock Provider) | {s[0]} | {s[1]} | {s[2]} |\\n",
        f"| OPA Policy (HTTP) | {o[0]} | {o[1]} | {o[2]} |\\n",
        f"| Audit Ledger (In-Memory) | {a[0]} | {a[1]} | {a[2]} |\\n",
        "\\n> [!NOTE]\\n> These are isolated component measurements, not end-to-end network latencies. Production latencies will vary significantly based on physical network distance to Redis, OPA, and the LLM API.\\n"
    ]
    lines = [l.replace("\\\\n", "\\n") for l in lines]
    with open("docs/performance-benchmark.md", "w") as f:
        f.writelines(lines)
    print("Measured component performance benchmark generated at docs/performance-benchmark.md")
"""

text = re.sub(r'async def run_benchmark\(args\):.*?print\("Measured component performance benchmark generated at docs/performance-benchmark.md"\)', new_func, text, flags=re.DOTALL)
text = text.replace('f.writelines([l.replace("\\n", "\\n") for l in lines])', 'f.writelines(lines)')
with open("scripts/cli.py", "w") as f:
    f.write(text)
