# Security Benchmark Report

## 1. Executive Summary
This report benchmarks the VILR Gateway Orchestrator against adversarial attacks and quantifies deterministic properties, semantic capabilities, and financial side-effects.

## 2. Attack Results

| Attack ID | Name | Classification | Expected | Actual | Defense Layer | HTTP | Calls | Creates | TxID | Duration (ms) | Error | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-01 | Indirect prompt injection through merchant metadata | BLOCKED | BLOCKED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 40.8 |  |  |
| T-02 | Semantic product substitution | BLOCKED | BLOCKED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 7.5 |  |  |
| T-03 | Cart tampering after signing | BLOCKED | BLOCKED | BLOCKED | Mandate Verifier | 400 | 0 | 0 |  | 0.8 |  |  |
| T-04 | Replay of a previously committed transaction | BLOCKED | BLOCKED | BLOCKED | Idempotency Store | 409 | 0 | 0 |  | 10.1 |  |  |
| T-05 | Over-budget transaction | BLOCKED | BLOCKED | BLOCKED | OPA Policy Engine | 400 | 0 | 0 |  | 8.3 |  |  |
| T-06 | Expired mandate | BLOCKED | BLOCKED | BLOCKED | Mandate Verifier | 400 | 0 | 0 |  | 0.8 |  |  |
| T-07 | Forged signature | BLOCKED | BLOCKED | BLOCKED | Mandate Verifier | 409 | 0 | 0 |  | 0.6 |  |  |
| T-08 | Concurrent duplicate execution | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 409 | 0 | 0 |  | 15.2 |  |  |
| T-09 | Maliciously malformed LLM output | BLOCKED | BLOCKED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 7.0 |  |  |
| T-10 | LLM timeout | BLOCKED | BLOCKED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 8.3 |  |  |
| T-11 | Agent impersonation | BLOCKED | BLOCKED | BLOCKED | Mandate Verifier | 409 | 0 | 0 |  | 0.9 |  |  |
| T-12 | Policy file tampering | BLOCKED | BLOCKED | BLOCKED | Policy Engine | 400 | 0 | 0 |  | 7.0 |  |  |
| T-13 | Audit tampering | DETECTED | DETECTED | DETECTED | Audit Ledger | 200 | 0 | 0 |  | 7.9 |  |  |
| T-14 | Key compromise | BLOCKED | BLOCKED | BLOCKED | Mandate Verifier | 409 | 0 | 0 |  | 0.8 |  |  |
| T-15 | OPA unavailable | BLOCKED | BLOCKED | BLOCKED | Policy Engine | 400 | 0 | 0 |  | 7.7 |  |  |
| T-16 | Execute without authorization | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 2.7 |  |  |
| T-17 | Another transaction's token | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.2 |  |  |
| T-18 | Reuse an execution token | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.3 |  |  |
| T-19 | Modify amount between authorize and execute | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.2 |  |  |
| T-20 | Modify merchant between authorize and execute | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.3 |  |  |
| T-21 | Modify mandate hash between authorize and execute | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.1 |  |  |
| T-22 | Replay with new transaction_id but same checkout | BLOCKED | BLOCKED | BLOCKED | Idempotency | 400 | 0 | 0 |  | 7.1 |  |  |
| T-23 | Replay after reservation expiration | BLOCKED | BLOCKED | BLOCKED | Idempotency | 400 | 0 | 0 |  | 7.0 |  |  |
| T-24 | Attempt to commit another transaction's Redis reservation | BLOCKED | BLOCKED | BLOCKED | Idempotency | 400 | 0 | 0 |  | 8.0 |  |  |
| T-25 | Attempt to release another transaction's Redis reservation | BLOCKED | BLOCKED | BLOCKED | Idempotency | 400 | 0 | 0 |  | 7.2 |  |  |
| T-26 | Conflicting provider idempotency-key reuse | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.3 |  |  |
| T-27 | PAYMENT_UNKNOWN double execution attempt | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.9 |  |  |
| T-28 | Unicode / normalization semantic trick | BLOCKED | DETECTED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 8.3 |  |  |
| T-29 | Very long merchant description | BLOCKED | BLOCKED | BLOCKED | API Validation | 400 | 0 | 0 |  | 6.6 |  |  |
| T-30 | Large cart / resource exhaustion | BLOCKED | BLOCKED | BLOCKED | API Validation | 400 | 0 | 0 |  | 7.4 |  |  |
| T-31 | Malformed nested JSON | BLOCKED | BLOCKED | BLOCKED | API Validation | 422 | 0 | 0 |  | 0.7 |  |  |
| T-32 | Unknown semantic enum value | BLOCKED | BLOCKED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 7.0 |  |  |
| T-33 | Invalid confidence value | BLOCKED | BLOCKED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 7.4 |  |  |
| T-34 | Missing semantic evidence | BLOCKED | BLOCKED | BLOCKED | Semantic Verifier | 400 | 0 | 0 |  | 7.4 |  |  |
| T-35 | Policy input type confusion | BLOCKED | BLOCKED | BLOCKED | Policy Engine | 400 | 0 | 0 |  | 9.2 |  |  |
| T-36 | Tampered audit record | BLOCKED | DETECTED | BLOCKED | Audit Ledger | 400 | 0 | 0 |  | 7.2 |  |  |
| T-37 | Deleted audit record | BLOCKED | DETECTED | BLOCKED | Audit Ledger | 400 | 0 | 0 |  | 10.8 |  |  |
| T-38 | Reordered audit record | BLOCKED | DETECTED | BLOCKED | Audit Ledger | 400 | 0 | 0 |  | 7.4 |  |  |
| T-39 | Broken prev_record_hash | BLOCKED | DETECTED | BLOCKED | Audit Ledger | 400 | 0 | 0 |  | 7.6 |  |  |
| T-40 | Replay of expired execution token | BLOCKED | BLOCKED | BLOCKED | Payment Executor | 422 | 0 | 0 |  | 0.3 |  |  |

## 3. Security Result Taxonomy

- BLOCKED: 17
- DETECTED: 1
- NOT_BLOCKED: 22
- ERROR: 0
- INCONCLUSIVE: 0

## 4. Side-Effect Metrics

- **Unauthorized Payment Execution Rate**: 0 / 40
- **Duplicate Payment Creation Rate**: 0 / 100

## 5. Deterministic Security Metrics

- **Hard Policy Bypass Rate**: 0 / 1
- **Replay Prevention Rate**: 1 / 1
- **Cart Tamper Detection Rate**: 1 / 1
- **Execution Authorization Bypass Rate**: 1 / 1
- **Duplicate Execution Rate**: 0 / 100
- **Audit Tamper Detection Rate**: 1 / 1
- **Malformed Input Rejection Rate**: 1 / 1

## 6. Semantic Security Metrics

*Note: This is a prototype adversarial measurement.*

- True Positives: 3
- False Positives: 0
- True Negatives: 2
- False Negatives: 0
- Semantic Detection Rate: 100%
- False Rejection Rate: 0%
- False Acceptance Rate: 0%

## 8. Layered Security Analysis

| Attack | Crypto protects? | Redis protects? | Semantic protects? | OPA protects? | Executor protects? | Audit detects? |
|---|---|---|---|---|---|---|
| Prompt Injection | No | No | Yes | No | No | No |
| Semantic Substitution | No | No | Yes | No | No | No |
| Cart Tampering | Yes | No | No | No | No | No |
| Replay Attack | No | Yes | No | No | No | No |
| Policy Bypass | No | No | No | Yes | No | No |
| Concurrent Execution | No | Yes | No | No | Yes | No |
| Audit Tampering | No | No | No | No | No | Yes |
