# OPA Policy Engine

The Open Policy Agent (OPA) serves as the deterministic final authorization authority in the VILR architecture.

## Responsibilities
- Deterministically evaluates hard policy constraints (budget, currency, merchant trust, expiration).
- Deterministically enforces semantic boundaries (rejecting `FAIL` or `REVIEW` transactions).
- Operates under a strict `default allow := false` paradigm.

## Non-Responsibilities
OPA **DOES NOT**:
- Execute payments.
- Track or enforce replay/idempotency (Redis handles this).
- Decode JWTs or verify ECDSA signatures (the crypto layer handles this).
- Modify the audit ledger or transaction state.

## Input Contract
The gateway submits a structured, flattened JSON payload to OPA representing the fully verified transaction intent and environmental state:

```json
{
  "mandate": {
    "exp": 1718000000,
    "max_amount": 50000.0,
    "currency": "INR",
    "allowed_merchants": ["merchant_dell"],
    "prohibited_merchants": [],
    "allowed_categories": ["laptop"],
    "prohibited_categories": []
  },
  "cart": {
    "merchant_id": "merchant_dell",
    "category": "laptop",
    "total_amount": 47999.0,
    "currency": "INR"
  },
  "semantic": {
    "status": "PASS",
    "confidence": 0.95
  },
  "current_time": 1717900000
}
```
*Note: Due to IEEE 754 precision, `max_amount` and `total_amount` must be mapped from `Decimal` to `float` for evaluation over Rego's `number` type at the boundaries.*

## Decision Schema
The output from OPA maps to `AuthorizationDecision`:
```json
{
  "allow": false,
  "violations": [
    {
      "code": "BUDGET_EXCEEDED",
      "message": "Cart total exceeds max amount"
    }
  ],
  "policy_version": "v1"
}
```

## Violation Codes
- `BUDGET_EXCEEDED`: Cart total exceeds mandate limit.
- `CURRENCY_MISMATCH`: Cart currency differs from mandate.
- `MERCHANT_NOT_ALLOWED`: Merchant not present in allowed list.
- `MERCHANT_PROHIBITED`: Merchant explicitly prohibited.
- `CATEGORY_NOT_ALLOWED`: Category not in allowed list.
- `CATEGORY_PROHIBITED`: Category explicitly prohibited.
- `MANDATE_EXPIRED`: Current time exceeds mandate expiration.
- `SEMANTIC_FAIL`: LLM flagged transaction as a semantic violation.
- `SEMANTIC_REVIEW`: LLM flagged transaction for review (resolves to DENY in secure mode).
- `INVALID_INPUT`: Required fields missing.
- `POLICY_DEFAULT_DENY`: Engine returned empty decision.

## Security Guarantees (The "LLM Override" Protection)
The engine strictly separates semantic scores from hard rules. An LLM's `confidence` score is evaluated, but it **cannot** bypass hard constraints. A transaction violating budget will be denied with `BUDGET_EXCEEDED`, even if the LLM marks it `PASS` with 0.999 confidence.

## Fail-Closed Behavior
If OPA is unreachable, times out, or returns a 500-level error, the gateway raises a `PolicyUnavailable` exception, dropping the request with an HTTP 503 equivalent. Under no circumstances does the gateway default to `ALLOW` during an outage.
