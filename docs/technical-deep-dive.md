# Technical Deep-Dive

**Cryptographic Binding:** Uses RFC 8785 JCS to canonically hash cart data, which is then signed via ES256 to create `checkout_hash`.
**Redis Reservation:** Employs a two-phase lock via `SETNX` (try_reserve) followed by Lua scripts for atomic `commit` (generating the execution token) and `release` upon failure.
**OPA Validation:** Restricts output to `AuthorizationDecision`. It never calls external APIs, ensuring sub-10ms evaluation times.
**Audit Hash Chain:** Uses SHA-256 hashing to link the previous transaction hash with the current transaction state, creating a localized immutable ledger.
**PAYMENT_UNKNOWN Handling:** Transitions to a non-terminal unknown state without retries, requiring a reconciliation polling worker to finalize safely.
