# Security Benchmark Report

## 1. Executive Summary
This report benchmarks the VILR Gateway Orchestrator against adversarial attacks and compares it with three baselines.

## 2. Attack Results

| Attack ID | Name | Baseline A | Baseline B | Baseline C | VILR | Defense Layer |
|---|---|---|---|---|---|---|
| T-01 | Indirect prompt injection through merchant metadata | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-02 | Semantic product substitution | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-03 | Cart tampering after signing | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Mandate Verifier |
| T-04 | Replay of a previously committed transaction | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Idempotency Store |
| T-05 | Over-budget transaction | NOT_BLOCKED | ERROR | NOT_BLOCKED | NOT_BLOCKED | OPA Policy Engine |
| T-06 | Expired mandate | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-07 | Forged signature | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-08 | Concurrent duplicate execution | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | Payment Executor |
| T-09 | Maliciously malformed LLM output | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-10 | LLM timeout | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-11 | Agent impersonation | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-12 | Policy file tampering | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Policy Engine |
| T-13 | Audit tampering | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | DETECTED | Audit Ledger |
| T-14 | Key compromise | NOT_BLOCKED | NOT_BLOCKED | BLOCKED | BLOCKED | Mandate Verifier |
| T-15 | OPA unavailable | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Policy Engine |
| T-16 | Execute without authorization | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-17 | Another transaction's token | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-18 | Reuse an execution token | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-19 | Modify amount between authorize and execute | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-20 | Modify merchant between authorize and execute | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-21 | Modify mandate hash between authorize and execute | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-22 | Replay with new transaction_id but same checkout | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Idempotency |
| T-23 | Replay after reservation expiration | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Idempotency |
| T-24 | Attempt to commit another transaction's Redis reservation | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Idempotency |
| T-25 | Attempt to release another transaction's Redis reservation | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Idempotency |
| T-26 | Conflicting provider idempotency-key reuse | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-27 | PAYMENT_UNKNOWN double execution attempt | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |
| T-28 | Unicode / normalization semantic trick | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-29 | Very long merchant description | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | API Validation |
| T-30 | Large cart / resource exhaustion | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | API Validation |
| T-31 | Malformed nested JSON | BLOCKED | BLOCKED | BLOCKED | BLOCKED | API Validation |
| T-32 | Unknown semantic enum value | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-33 | Invalid confidence value | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-34 | Missing semantic evidence | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Semantic Verifier |
| T-35 | Policy input type confusion | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Policy Engine |
| T-36 | Tampered audit record | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Audit Ledger |
| T-37 | Deleted audit record | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Audit Ledger |
| T-38 | Reordered audit record | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Audit Ledger |
| T-39 | Broken prev_record_hash | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | NOT_BLOCKED | Audit Ledger |
| T-40 | Replay of expired execution token | BLOCKED | BLOCKED | BLOCKED | BLOCKED | Payment Executor |

## 3. Security Metrics

- Total Attacks: 40
- BLOCKED: 17
- DETECTED: 1
- NOT_BLOCKED: 22
- ERROR: 0
- INCONCLUSIVE: 0
- Security Success Rate: 45.0% (Calculated as [BLOCKED + DETECTED] / Total)
