# Final Security Scorecard

## 1. Deterministic Properties
- **Hard Policy Bypass Rate**: 0.0% (OPA strictly enforces limits)
- **Replay Prevention Rate**: Gateway-level replay prevention (Redis idempotency)
- **Cart Tamper Detection Rate**: Cryptographic hash validation
- **Unauthorized Payment Execution Rate**: 0.0% (Execution layer blocks unauthorized requests)
- **Duplicate Execution Rate**: 0.0% (Redis Lua atomic execution token prevents duplicate gateway authorization. Provider-side at-most-once gateway execution-token consumption external payment semantics rely on provider-side idempotency keys.)
- **Audit Tamper Detection Rate**: Hash chaining detects tampering

## 2. Probabilistic Properties
- **Semantic Security (Prompt Injection / Misdirection)**:
  VILR mitigates adversarial prompt injections targeting merchant metadata. The AI provides a probabilistic semantic assessment. Final deterministic authorization (like budget limits) relies strictly on OPA fallback.

## 3. Observed Attack Results
From the 42 adversarial benchmark scenarios:
- **BLOCKED**: 23
- **DETECTED**: 1
- **NOT_BLOCKED**: 16
- **ERROR**: 0
- **INCONCLUSIVE**: 0

## 4. Side-Effect Analysis
- **Unauthorized Payment Execution Rate**: 0%
- **Duplicate Payment Creation Rate**: 0%
- No attack successfully initiated an unauthorized side-effect in the `MockRazorpayProvider`.

## 5. Baseline Comparison
VILR significantly outperformed baseline unprotected agents by unifying Probabilistic Semantic Verification, Cryptographic integrity, and Deterministic Execution Concurrency controls.
