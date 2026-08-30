# VILR (Verifiable Intent Ledger & Resolver)

VILR is a high-security gateway orchestrator designed to safely authorize and execute financial transactions initiated by autonomous, non-deterministic AI agents.

## Architecture

VILR employs a layered defense architecture:
1. **Cryptography**: Mandate sealing via JWT and SHA-256 cart hashing.
2. **Idempotency**: Redis-backed replay protection.
3. **Semantic AI**: AI-driven verification of user intent vs. cart contents (Fail-closed).
4. **Deterministic Policy**: OPA (Open Policy Agent) for strict financial constraints.
5. **Execution Token**: Atomic, single-use token consumption via Lua scripts for concurrency protection.
6. **Audit Ledger**: Hash-chained, immutable transaction history.

## Getting Started

### Requirements
- Python 3.12+
- Redis (for idempotency and concurrency locks)
- Open Policy Agent (OPA)

### Running Demos and Benchmarks
Use the built-in CLI to run deterministic demos and security benchmarks:

```bash
# Run the interactive demo (8 scenarios)
python -m scripts.cli demo

# Run the full 40-attack security benchmark
python -m scripts.cli security

# Generate baseline comparisons
python -m scripts.cli security --baseline

# Run performance benchmarks
python -m scripts.cli benchmark

# Verify an audit chain
python -m scripts.cli audit verify <transaction_id>
```

## Documentation
- [Security Benchmark](docs/security-benchmark.md)
- [Baseline Comparison](docs/baseline-comparison.md)
- [Performance Benchmark](docs/performance-benchmark.md)
- [Final Security Scorecard](docs/final-security-scorecard.md)
