# VILR Idempotency & Replay Protection

This document outlines the idempotency and replay protection mechanisms inside VILR's Gateway orchestrator.

## Why Redis?
VILR uses Redis to manage a high-performance, atomic, distributed lock system for transaction authorization. It provides race-free, two-phase authorization reservations.
**Crucially: Redis does not guarantee at-most-once gateway execution external payment execution.** Provider-side payment idempotency is handled independently by passing a provider-specific idempotency key during the execution phase. Redis simply ensures the gateway itself evaluates and authorizes a checkout at most once.

## Composite Key
The canonical idempotency key is a composite of the open mandate hash and the specific checkout hash:
`vilr:idempotency:{open_mandate_hash}:{checkout_hash}`

This composite identity ensures:
- The same checkout submitted twice hits the same reservation key (preventing replay).
- Different checkouts under the same open mandate hit different reservation keys, allowing independent processing without falsely triggering replay limits.

## Reservation Lifecycle (Two-Phase)
1. **ABSENT**: No transaction has reserved this key.
2. **RESERVED**: A transaction tentatively acquires the lock. It has exclusive ownership.
3. **COMMITTED**: The transaction successfully passed semantic and policy validation. The reservation is permanently sealed.

### Operations
- `try_reserve`: Uses a `SETNX` equivalent primitive. It conditionally creates the record with a tentative TTL (e.g., 300s).
- `commit`: Verifies ownership via Lua script, checks that status is `reserved` (or already `committed` for idempotency), sets status to `committed`, and extends the TTL (e.g., 24h).
- `release`: Verifies ownership via Lua script, ensures the status is `reserved`, and deletes the key, allowing future retries (used on semantic or policy failure).

## Concurrency & Atomicity
VILR is safe against concurrent authorization requests for the same checkout.
If N requests arrive concurrently for `M:A`:
- The Redis atomic `SETNX` guarantees exactly 1 request acquires the `reserved` state.
- The remaining N-1 requests immediately fail the `try_reserve` attempt and revert as duplicates.

## Ownership
Every reservation contains a unique `transaction_id`. Only the transaction holding the matching `transaction_id` can `commit` or `release` the reservation. This prevents cross-transaction interference where a failing concurrent attempt might accidentally release a successful attempt's lock.

## TTL (Time To Live)
- **Tentative TTL**: Short (default 300s). If the VILR gateway crashes after acquiring a reservation but before completing validation, the lock automatically releases, preventing a permanent denial of service for that checkout.
- **Committed TTL**: Longer (default 24h+). Preserves the replay protection window for a reasonable duration after a successful transaction. It is not a hard security boundary, but a functional replay window.

## Failure Behavior
If Redis is unavailable, VILR **fails closed**.
It immediately rejects the request with an HTTP 503 equivalent (`IdempotencyUnavailable`). It will NOT fall back to processing without a reservation, as that would risk concurrent duplicate executions.

## Gateway Reservation vs. Provider Idempotency
- **Gateway Reservation**: Ensures VILR evaluates policy and semantically analyzes the intent at most once.
- **Provider Idempotency**: Ensures the Payment Provider charges the user at most once, even in the event of `PAYMENT_UNKNOWN` timeouts and retries.
