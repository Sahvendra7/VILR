# Gateway Orchestrator (Phase 7)

## Overview
The `GatewayOrchestrator` is the central nervous system of VILR. It unifies isolated domain components (Crypto, Redis, Semantic, Policy, Executor, Audit) into coherent, state-bound transaction flows.

## Responsibilities
- **Authorization Flow**: Sequences AP2 verification, Cartesian verification, Redis idempotency reservation, LLM semantic validation, and OPA policy evaluation. Returns an opaque `execution_token` upon success.
- **Execution Flow**: Consumes single-use execution tokens mapped securely to authorized payload hashes to trigger `PaymentExecutor`.
- **Unknown Reconciliation**: Maps ambiguous `UNKNOWN` payment states explicitly via `resolve_unknown()`.
- **Audit Emissions**: Appends verifiable cryptographically-linked `AuditRecord` objects to the `AuditLedger` during all transition phases.

## State Management and Safety Properties
1. **Never Fail Open**: Failure in Crypto, Redis, Semantic Verifier, or OPA immediately denies execution.
2. **Deterministic Release**: A failed reservation attempt (before OPA) releases tentative locks on Redis.
3. **Immutability of Execution Context**: `execution_token` bindings strictly map `(amount, currency, merchant_id, mandate_hash)`. Tampering between auth and exec aborts the flow.
4. **No Internal Retries**: Re-running execution on `PAYMENT_UNKNOWN` is strictly forbidden. Polling `get_payment_status()` is mandatory to resolve ambiguity.
