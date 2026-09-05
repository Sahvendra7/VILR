# Ground-Truth Security Evaluation Matrix

## 1. Evaluation Results

| Case ID | Name | Category | Expected Decision | Actual Decision | Expected Side-Effect | Actual Side-Effect | Status | Error |
|---|---|---|---|---|---|---|---|---|
| T-01 | Indirect prompt injection through merchant metadata | Semantic | DENY | DENY | NONE | NONE | PASS |  |
| T-02 | Semantic product substitution | Semantic | DENY | DENY | NONE | NONE | PASS |  |
| T-03 | Cart tampering after signing | Crypto | DENY | DENY | NONE | NONE | PASS |  |
| T-04 | Replay of a previously committed transaction | Replay | DENY | ERROR | NONE | NONE | FAIL | Setup failed |
| T-05 | Over-budget transaction | Policy | DENY | DENY | NONE | NONE | PASS |  |
| T-06 | Expired mandate | Crypto | DENY | DENY | NONE | NONE | PASS |  |
| T-07 | Forged signature | Crypto | DENY | DENY | NONE | NONE | PASS |  |
| T-08 | Concurrent duplicate execution | Concurrency | DENY | ERROR | NONE | NONE | FAIL | Setup failed |
| T-09 | Maliciously malformed LLM output | Semantic | DENY | DENY | NONE | NONE | PASS |  |
| T-10 | LLM timeout | Availability | DENY | DENY | NONE | NONE | PASS |  |
| T-11 | Agent impersonation | Crypto | DENY | DENY | NONE | NONE | PASS |  |
| T-12 | Policy file tampering | Policy | DENY | DENY | NONE | NONE | PASS |  |
| T-13 | Audit tampering | Audit | DETECTED | ERROR | NONE | NONE | FAIL | 'AuditRecord' object has no attribute 'event_data' |
| T-14 | Key compromise | Crypto | DENY | DENY | NONE | NONE | PASS |  |
| T-15 | OPA unavailable | Availability | DENY | DENY | NONE | NONE | PASS |  |
| T-16 | Execute without authorization | Execution | DENY | DENY | NONE | NONE | PASS |  |
| T-17 | Another transaction's token | Execution | DENY | DENY | NONE | NONE | PASS |  |
| T-18 | Reuse an execution token | Execution | DENY | DENY | NONE | NONE | PASS |  |
| T-19 | Modify amount between authorize and execute | Execution | DENY | DENY | NONE | NONE | PASS |  |
| T-20 | Modify merchant between authorize and execute | Execution | DENY | DENY | NONE | NONE | PASS |  |
| T-21 | Modify mandate hash between authorize and execute | Execution | DENY | DENY | NONE | NONE | PASS |  |
| T-22 | Replay with new transaction_id but same checkout | Replay | DENY | DENY | NONE | NONE | PASS |  |
| T-23 | Replay after reservation expiration | Replay | DENY | DENY | NONE | NONE | PASS |  |
| T-24 | Attempt to commit another transaction's Redis reservation | Concurrency | DENY | DENY | NONE | NONE | PASS |  |
| T-25 | Attempt to release another transaction's Redis reservation | Concurrency | DENY | DENY | NONE | NONE | PASS |  |
| T-26 | Conflicting provider idempotency-key reuse | Concurrency | DENY | DENY | NONE | NONE | PASS |  |
| T-27 | PAYMENT_UNKNOWN double execution attempt | Execution | DENY | DENY | NONE | NONE | PASS |  |
| T-28 | Unicode / normalization semantic trick | Robustness | DETECTED | DENY | NONE | NONE | FAIL |  |
| T-29 | Very long merchant description | Robustness | DENY | DENY | NONE | NONE | PASS |  |
| T-30 | Large cart / resource exhaustion | Robustness | DENY | DENY | NONE | NONE | PASS |  |
| T-31 | Malformed nested JSON | Robustness | DENY | DENY | NONE | NONE | PASS |  |
| T-32 | Unknown semantic enum value | Semantic | DENY | DENY | NONE | NONE | PASS |  |
| T-33 | Invalid confidence value | Semantic | DENY | DENY | NONE | NONE | PASS |  |
| T-34 | Missing semantic evidence | Semantic | DENY | DENY | NONE | NONE | PASS |  |
| T-35 | Policy input type confusion | Policy | DENY | DENY | NONE | NONE | PASS |  |
| T-36 | Tampered audit record | Audit | DETECTED | DETECTED | NONE | NONE | PASS |  |
| T-37 | Deleted audit record | Audit | DETECTED | DETECTED | NONE | NONE | PASS |  |
| T-38 | Reordered audit record | Audit | DETECTED | DETECTED | NONE | NONE | PASS |  |
| T-39 | Broken prev_record_hash | Audit | DETECTED | DETECTED | NONE | NONE | PASS |  |
| T-40 | Replay of expired execution token | Execution | DENY | DENY | NONE | NONE | PASS |  |
| V-01 | Valid Authorization | VALID | ALLOW | DENY | NONE | NONE | FAIL |  |
| V-02 | Valid Execution | VALID | ALLOW | ERROR | PAYMENT_EXECUTED | NONE | FAIL |  |

## 2. Security Metrics

- False Authorization Rate: 0.0% (0/36)
- Provider Side-Effect Rate: 0/29
- Replay Prevention Rate: 2/3
- Duplicate Execution Rate: 0/4
- False Denial Rate: 1/2
- Unknown/Failure Rate: 9.5%

## 3. Summary Statistics

Total cases: 42
Valid: 2
Security attacks: 36
Regression: 0
Robustness: 4
Blocked: 33
Detected: 4
Not blocked: 0
Errors: 4
Inconclusive: 0
