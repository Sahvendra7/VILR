# Final Claims Review

## 1. Deterministic Security Claims
**Found:** `docs/final-security-scorecard.md` contained outdated benchmark numbers (40 tests, 22 NOT_BLOCKED).
**Correction:** Adjusted to match the verified 186 total tests (180 BLOCKED, 6 DETECTED, 0 NOT_BLOCKED).
**Found:** Scorecard stated "Redis Lua atomic execution token prevents double spend."
**Correction:** Adjusted to "Redis Lua atomic execution token prevents duplicate gateway authorization. at-most-once gateway execution-token consumption external payments rely on provider-side idempotency keys."

## 2. Legal / Liability Claims
**Found:** `README.md` mentions "liability is undefined". 
**Correction:** Clarified that VILR provides *tamper-evident audit logs* for dispute resolution, but does *not* automatically transfer or assume legal liability.

## 3. AI Determinism Claims
**Found:** `docs/final-security-scorecard.md` claimed "VILR successfully blocks adversarial prompt injections... because AI models independently evaluate structured JSON."
**Correction:** Rewritten to reflect that AI is purely *probabilistic*. AI *detects* semantic mismatches; OPA *deterministically blocks* unauthorized executions.

## 4. Cryptography and Payment Execution
**Found:** No claims found implying cryptography executes payments. Cryptography strictly *verifies* intent-to-cart integrity.

## 5. OPA and Prompt Injection
**Found:** Ensured no documentation implies OPA natively detects prompt injections. OPA only evaluates the probabilistic `SemanticAssessment` evidence alongside deterministic budget constraints.

## 6. Redis and at-most-once gateway execution-token consumption Payments
**Found:** Documentation accurately distinguishes between Gateway-level execution tokens (Redis) and Provider-level idempotency (Razorpay/Mock provider).

## 7. AP2 Compliance
**Found:** `docs/limitations.md` correctly states "Simplified AP2-compatible representation". No claims of full protocol compliance were found.

## 8. Taxonomy Consistency
**Status:** Enforced consistent usage of `BLOCKED`, `DETECTED`, `NOT_BLOCKED`, `ERROR`, `INCONCLUSIVE` across all scorecard and benchmark reports.

## 9. Performance Latency
**Status:** `docs/performance-benchmark.md` explicitly isolates deterministic gateway latency (~10ms) from probabilistic LLM latency (~850ms+).
