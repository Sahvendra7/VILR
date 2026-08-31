# Interview Preparation (Judge Questions)

**Q1: What if the AI hallucinates a PASS?**
- 1-Sentence: OPA still strictly enforces the budget and allowed merchant list.
- 30-Second: The semantic assessment is merely untrusted evidence fed into OPA. If the AI returns 99.9% confidence for a $500 cart on a $100 budget limit, OPA statically denies it.
- Deep: `SemanticAssessment` is parsed as a typed object and injected into OPA Rego context. `allow == false` if `input.cart.total_amount > input.mandate.max_amount`, completely ignoring `input.semantic.status`.
- Evidence: `test_security_llm_cannot_override_budget`.

**Q2: Why not just use OAuth?**
- 1-Sentence: OAuth authorizes *who* the agent is, not *what* the transaction is.
- 30-Second: OAuth delegates scopes (e.g. `payment:write`). Once an agent has the token, it can execute *any* payment. VILR authorizes the specific payload cryptographically tied to the user intent.
- Deep: We separate Authenticity, Replay Protection, and Authorization. OAuth handles Authenticity but fails at intent-binding.
- Evidence: `architecture.md`.

**Q3: How do you prevent replay attacks?**
- 1-Sentence: Using a composite Redis key (`open_mandate_hash:checkout_hash`) and an atomic execution token.
- 30-Second: Before authorization, we `SETNX` a reservation key in Redis. If multiple identical requests hit the gateway, only one gets the reservation. The winner gets an execution token.
- Deep: Lua scripting handles atomic commit.
- Evidence: `test_concurrent_execution` hitting 100x requests.

**Q4: What if Redis goes down?**
- 1-Sentence: VILR fails closed. No reservation = no payment.
- 30-Second: If Redis is unavailable, the `try_reserve` throws a ConnectionError which is caught by the Gateway, returning a 503 HTTP Service Unavailable.
- Deep: Safe failure defaults to DENY.
- Evidence: `test_redis_unavailable` integration test.
