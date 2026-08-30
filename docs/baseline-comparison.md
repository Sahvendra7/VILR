# Baseline Comparison

| Attack | Category | Baseline A | Baseline B | Baseline C | VILR | Security Property Added |
|---|---|---|---|---|---|---|
| T-01 | Semantic | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-02 | Semantic | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-03 | Crypto | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Mandate Verifier |
| T-04 | Replay | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | ERROR | Idempotency Store |
| T-05 | Policy | NOT_BLOCKED | ERROR | NOT_BLOCKED | BLOCKED | OPA Policy Engine |
| T-06 | Crypto | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-07 | Crypto | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-08 | Concurrency | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | ERROR | Payment Executor |
| T-09 | Semantic | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-10 | Availability | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-11 | Crypto | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-12 | Policy | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Policy Engine |
| T-13 | Audit | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | DETECTED | Audit Ledger |
| T-14 | Crypto | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-15 | Availability | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Policy Engine |
| T-16 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-17 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-18 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-19 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-20 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-21 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-22 | Replay | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Idempotency |
| T-23 | Replay | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Idempotency |
| T-24 | Concurrency | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Idempotency |
| T-25 | Concurrency | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Idempotency |
| T-26 | Concurrency | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-27 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-28 | Semantic | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-29 | Availability | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | API Validation |
| T-30 | Availability | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | API Validation |
| T-31 | API | BLOCKED | BLOCKED | BLOCKED | BLOCKED | API Validation |
| T-32 | Semantic | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-33 | Semantic | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-34 | Semantic | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Semantic Verifier |
| T-35 | Policy | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Policy Engine |
| T-36 | Audit | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Audit Ledger |
| T-37 | Audit | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Audit Ledger |
| T-38 | Audit | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Audit Ledger |
| T-39 | Audit | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Audit Ledger |
| T-40 | Execution | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
