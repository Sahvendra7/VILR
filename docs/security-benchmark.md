# VILR Security Benchmark (Phase 8 Results)

## 1. Adversarial Results
Total attacks evaluated: 40

| Classification | Count | Description |
|---|---|---|
| **BLOCKED** | 16 | Attack prevented from executing payment (e.g. OPA denial, Redis conflict) |
| **DETECTED** | 1 | Attack detected and stopped, but reached an intermediate failure state |
| **NOT_BLOCKED** | 23 | Attack bypassed security controls (Execution Layer Vulnerabilities, Semantic Drifts) |
| **ERROR** | 0 | Test harness errors |
| **INCONCLUSIVE** | 0 | Unknown state |

**Security Success Rate:** 42.5% ((16 + 1) / 40)

## 2. Component Efficacy
- **Gateway-level Replay Prevention:** High reliability (via Redis idempotency)
- **Duplicate Execution Prevention:** High reliability (via Token consumption atomicity, fixed in Phase 8.5)
- **Cart Tamper Detection Rate:** High reliability (via JCS Cryptographic hash validation)
- **Audit Tamper Detection Rate:** High reliability (via in-memory hash chaining)

> [!NOTE]
> The benchmark is an adversarial instrument. The 23 NOT_BLOCKED attacks explicitly target probabilistic boundaries (LLM prompt injections) and prototype limitations (like concurrent executions that were subsequently remediated in Phase 8.5).
