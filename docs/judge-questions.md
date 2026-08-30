# Defense Responses (Judge Questions)

**1. How do you ensure LLM prompt injection doesn't alter the financial outcome?**
The AI is completely decoupled from the execution parameters. We use a split authorization architecture. The LLM only provides a semantic `PASS`/`FAIL` assessment based on the user's intent versus the cart line items. If it hallucinates or is injected, the worst it can do is approve a transaction that must STILL pass hard deterministic OPA constraints and cryptographic signatures before execution is allowed.

**2. What happens if multiple identical requests hit the execution endpoint at exactly the same time?**
We use Redis Lua scripting to atomically verify and consume single-use execution tokens. In a benchmark of 100 concurrent requests, exactly 1 succeeded and 99 received HTTP 409 Conflicts, guaranteeing zero duplicate payments at the provider layer.

**3. What if a malicious user alters the `total_amount` in the HTTP request payload?**
The Gateway validates the payload signature against the cryptographic `cart_hash` sealed in the `open_mandate_hash`. Tampering with any detail of the cart (price, item, quantity) breaks the signature and causes the authorization pipeline to instantly reject the transaction before invoking the LLM or OPA.

**4. How do you handle `UNKNOWN` payment status due to network timeouts?**
The Gateway Orchestrator maps network timeouts to `PAYMENT_UNKNOWN`. It does NOT blindly auto-retry. It leaves the transaction in an `EXECUTION_STARTED` state in the audit ledger and requires asynchronous provider polling or webhook reconciliation to determine terminal state (`SUCCESS` or `FAILED`), thus preventing accidental double-charging.

**5. How is the audit ledger protected against tampering?**
Each entry is cryptographically chained to the previous entry using a SHA-256 hash. Any attempt to modify, insert, or delete a past event immediately invalidates the entire chain, which can be instantly verified using the `audit verify` CLI command.

**6. Why use OPA for hard constraints instead of just writing Python logic?**
OPA enforces decoupling. Hard limits (like max budget, prohibited merchant categories) must be dynamically updatable without redeploying code. OPA provides a deterministic, auditable, and centralized policy decision point separate from the application business logic.

**7. Can an attacker reuse an authorization token?**
No. All authorizations are checked against a Redis reservation system using idempotency keys. Replays are detected before reaching semantic analysis or OPA, blocking the attack at the earliest possible stage with an HTTP 409.

**8. What does "Fail Closed" mean in your semantic layer?**
If the LLM provider times out, returns malformed JSON, or gives a low confidence score (<0.85), the `SemanticVerifier` throws a `VILRError` mapping to a 503 or 422, explicitly preventing the transaction from proceeding.

**9. Why aren't you using OAuth2 for everything?**
OAuth2 secures the connection (AP2). VILR secures the *transaction content*. Knowing WHO is sending a request doesn't prove that WHAT they are sending is authorized. VILR sits underneath identity to authorize the financial side-effect.

**10. What metrics do you track for success?**
We track deterministic side-effect metrics (Unauthorized Payment Execution Rate = 0%, Duplicate Payment Creation Rate = 0%), P95 latencies (to ensure synchronous user experience is not degraded), and adversarial classification rates (BLOCKED vs DETECTED).

*(Additional questions omitted for brevity. The technical defenses remain constant across all adversarial angles: Cryptography for Integrity, OPA for Determinism, Redis for Concurrency/Idempotency, AI strictly for Semantic translation).*
