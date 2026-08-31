# PAYMENT_UNKNOWN Validation

When a provider times out, the Gateway safely transitions the state to `UNKNOWN`.

- **No automatic retry:** VILR does not automatically issue a new execution to prevent double-charging.
- **Execution token consumed:** The Gateway strictly consumes the execution token.
- **Audit Consistency:** The `UNKNOWN` state is hashed into the ledger.
- **Reconciliation to SUCCESS:** Validates payment with provider, updates audit ledger to SUCCESS without executing new payment.
- **Reconciliation to FAILED:** Validates payment failure with provider, updates audit ledger to FAILED without retrying.
