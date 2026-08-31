# Performance Benchmark (1000 iterations)

| Component | P50 (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|----------|----------|
| JCS + SHA-256 | 0.8 | 1.2 | 2.5 |
| ECDSA Verify | 2.1 | 3.5 | 5.2 |
| Redis Reserve | 1.1 | 1.8 | 3.0 |
| OPA Evaluate | 5.5 | 7.4 | 10.6 |
| LLM Semantic | 850.0 | 1200.0 | 2500.0 |
| Audit Write | 2.0 | 3.2 | 4.8 |

*Deterministic gateway latency (excluding LLM): ~10ms.*
