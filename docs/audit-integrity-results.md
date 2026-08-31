# Audit-Chain Validation

Baseline status: VALID (SHA-256 hash chains intact).

| Attack Type | Detected | Response |
|-------------|----------|----------|
| Record mutation | YES | `chain_valid=False`, index identified. |
| Deletion | YES | Previous hash mismatch at `i+1`. |
| Reordering | YES | Temporal mismatch and hash mismatch. |
| prev_record_hash mutation | YES | Structural validation failure. |
| record_hash mutation | YES | Data re-hash mismatch. |
