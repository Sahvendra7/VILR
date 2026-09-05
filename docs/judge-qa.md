# VILR: Judge Q&A

### 1. Why is an LLM needed?
To prevent semantic substitution attacks. Cryptography ensures the cart wasn't tampered with, but an LLM ensures the items in the cart actually match the user's natural language intent.

### 2. Why isn't cryptography enough?
Cryptography proves *who* signed *what* data, but it cannot prove *whether the data is what the user actually wanted*. A malicious merchant could perfectly sign a $1000 Apple Gift Card when the user originally asked their agent to buy "$1000 worth of dog food".

### 3. What happens if Gemini is wrong?
The system relies on a "fail-closed" semantic verification. If Gemini falsely passes a bad transaction, the deterministic Open Policy Agent (OPA) still enforces hard constraints (e.g., maximum budget, merchant whitelists). If Gemini falsely fails a good transaction, the payment is blocked (false positive), protecting the user's funds.

### 4. Can Gemini authorize payment?
**No.** Gemini produces probabilistic semantic evidence (a `PASS`/`FAIL` assessment). OPA consumes this evidence alongside cryptographic checks and makes the final, deterministic authorization decision.

### 5. Why OPA?
Open Policy Agent (OPA) provides a decoupled, deterministic, and auditable policy engine. It ensures that authorization logic remains completely isolated from the probabilistic nature of the LLM.

### 6. Why Redis?
Redis enforces Gateway-level replay prevention and idempotency. It uses atomic Lua scripts (`SETNX`) to guarantee that a single intent can only generate exactly one execution token, preventing double-spends before the payment provider is even contacted.

### 7. What happens under concurrency?
If 100 concurrent execution requests arrive for the same transaction, Redis processes them atomically. Exactly 1 request acquires the lock and proceeds to the payment provider. The other 99 requests are rejected instantly at the Gateway with a `409 Conflict`.

### 8. What happens if the provider times out?
The system returns a `PAYMENT_UNKNOWN` state. Because distributed systems cannot distinguish between a dropped request and a dropped response, VILR does not automatically retry. Instead, it enters a reconciliation state to prevent accidental duplicate charges.

### 9. Why AP2-compatible instead of AP2-compliant?
VILR represents the core concepts of the Advanced Payments 2.0 (AP2) specification (e.g., mandate binding, cryptographic signatures) using a lightweight JSON/JCS implementation suitable for a hackathon prototype, rather than requiring the heavy infrastructure of full AP2 compliance.

### 10. Why Mock Razorpay?
To safely demonstrate end-to-end security invariants and failure modes (like network timeouts and concurrency conflicts) locally without risking live financial endpoints or requiring real money.

### 11. What would production deployment change?
A production deployment would integrate a real HSM (Hardware Security Module) for key management, a production Razorpay gateway API integration, highly available OPA/Redis clusters, and distributed tracing.

### 12. How does this recover revenue?
By providing a safe boundary for autonomous agents, merchants can deploy automated systems to negotiate failed payments, offer alternative products, or automatically retry recoverable failures (like temporary provider outages) with confidence that the agent cannot be manipulated into authorizing malicious transactions.

### 13. How do you prevent retries from creating duplicate payments?
Retries are protected by dual-layer idempotency: Redis ensures at-most-once consumption of the VILR execution token at the Gateway, and an Idempotency-Key header is passed to the payment provider for downstream protection.

### 14. What does the security benchmark actually prove?
It proves that within the 40 modeled attack scenarios (including prompt injection, cart tampering, and concurrent replays), the VILR Gateway correctly identified and blocked unauthorized state transitions, protecting the simulated execution endpoint.

### 15. What does it NOT prove?
It does not guarantee 100% security against unmodeled zero-day attacks, LLM jailbreaks that perfectly mimic legitimate transactions, or underlying hardware/cryptographic vulnerabilities.

### 16. What does the Razorpay TEST integration prove?
It proves that VILR's internal execution token semantics map successfully to a real external Payment Gateway (Razorpay TEST API), allowing actual authorized side-effects to be executed safely after passing the cryptographic and semantic gauntlet.

### 17. What does Supabase provide?
Supabase provides a persistent tamper-evident audit chain. Every decision and execution step is logged with a `prev_record_hash`. This cryptographic chaining guarantees that any retroactive tampering by an attacker is immediately detectable.

### 18. Why is RLS disabled?
Row Level Security (RLS) is disabled because this is a hackathon prototype demonstrating application-level cryptographic tamper evidence. In a production environment, RLS would be strictly enforced, and append-only cloud logging (WORM storage) would be used.
