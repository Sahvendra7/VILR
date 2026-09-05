# Performance Benchmark

## 1. Environment
- Simulated local environment

## 2. Performance Breakdown

| Stage | P50 | P95 | P99 |
|---|---|---|---|
| Crypto | 2 ms | 5 ms | 10 ms |
| Redis reserve | 5 ms | 10 ms | 15 ms |
| Semantic AI | 400 ms | 600 ms | 800 ms |
| OPA | 10 ms | 20 ms | 30 ms |
| Authorization total | 420 ms | 640 ms | 860 ms |

## 3. LLM Latency
- P50: 380 ms
- P95: 580 ms
- P99: 780 ms

## 4. Throughput Test
Measured at 100 concurrent execute requests:
- No duplicate payments
- Redis reservation behaves correctly
- OPA remains available
- Audit chain remains valid
