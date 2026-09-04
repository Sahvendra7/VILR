# Performance Benchmark

## 1. Environment
- Component-level measurements in local Python runtime (100 iterations)

## 2. Component Performance Breakdown (Measured)

| Component | P50 | P95 | P99 |
|---|---|---|---|
| Crypto Verifier (JCS + ECDSA) | 0.18 ms | 0.51 ms | 0.53 ms |
| Idempotency (Fakeredis memory) | 0.00 ms | 0.00 ms | 0.00 ms |
| Semantic AI (Mock Provider) | 0.02 ms | 0.05 ms | 3.16 ms |
| OPA Policy (HTTP Timeout expected) | 3.06 ms | 6.41 ms | 21.31 ms |
| Audit Ledger (In-Memory) | 0.05 ms | 0.14 ms | 0.28 ms |

> [!NOTE]
> These are isolated component measurements, not end-to-end network latencies. Production latencies will vary significantly based on physical network distance to Redis, OPA, and the LLM API.
