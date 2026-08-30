# Audit Ledger (Phase 7)

## Overview
The VILR Audit Ledger generates an append-only, sequentially verified cryptographic hash chain tracking all significant mutations of the state machine.

## Structure
Every `AuditRecord` includes key deterministic data points:
- `transaction_id`, `user_id`, `merchant_id`
- Contextual integrity hashes (`open_mandate_hash`, `cart_hash`)
- Authorization outputs (`policy_decision`, `semantic_confidence`)

### The Hash Chain
The VILR Ledger guarantees sequence integrity using chained SHA-256 links built upon RFC 8785 JSON Canonicalization (JCS):
1. The genesis record links to a documented `GENESIS_HASH` (`"0" * 64`).
2. Each subsequent record embeds the `record_hash` of its predecessor as `prev_record_hash`.
3. Validating the chain recalculates canonical hashes end-to-end to detect modifications, reorderings, and deletions.

## Verifiability
Through the API endpoint `/v1/audit/{transaction_id}/verify`, third-party auditors can mathematically verify that no semantic drift failures or policy denials were bypassed, providing absolute transparent proof of compliance.
