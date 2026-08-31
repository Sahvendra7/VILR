# Architecture

1. **User Intent** -> AI Agent -> Merchant Cart
2. **Merchant Checkout** -> Gateway (Intent + Cart + Signatures)
3. **Gateway Crypto** -> Verifies Signatures & JCS Hashes
4. **Gateway Semantic** -> Probabilistic Intent Matching (PASS/REVIEW/FAIL)
5. **Gateway OPA** -> Deterministic Authorization (Budget/Category/Semantic)
6. **Gateway Idempotency** -> Redis Two-Phase Reservation
7. **Gateway Execution** -> Consumes Token -> Payment Provider API
8. **Gateway Audit** -> Appends to Tamper-Evident Ledger
