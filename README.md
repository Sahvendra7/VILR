# VILR 2.0: Zero-Trust Agentic Payments

**AI agents can decide what to buy. They should not be allowed to decide whether money can move.**

VILR is a cryptographically verifiable, deterministic authorization gateway for agent-driven commerce. 

- **AI understands** (Semantic evaluation of intent)
- **Crypto verifies** (JCS + ECDSA P-256 signatures)
- **OPA authorizes** (Deterministic policy evaluation)
- **Redis protects execution** (Atomic two-phase idempotency)
- **Payment provider executes** (Mock/Razorpay endpoints)
- **Audit records evidence** (Tamper-evident hash chain)

## Problem & Why It Matters
Agents hallucinate. Merchants can be malicious. If an agent executes a payment directly, liability is undefined, and prompt injection can drain wallets.

## Core Insight
Split the intelligence from the authorization. Let AI negotiate, but enforce the transaction with cryptographic boundaries.

## Architecture
See `docs/architecture-final.md`.

## Trust Boundaries & Security Model
See `docs/security-model-final.md`.

## Quickstart & Demo
```bash
python -m scripts.cli demo
python -m scripts.cli hero
python -m scripts.cli security-demo
```

## Security & Architecture
For details on the architecture, baseline comparisons, and the strict zero-trust threat model, please consult the `docs/` directory.
