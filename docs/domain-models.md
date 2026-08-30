# Domain Models & Architecture

## Money Handling
**Decision:** We are using `decimal.Decimal` (represented in Pydantic as `condecimal(ge=0)` or `Annotated[Decimal, Field(ge=0)]`) for all monetary values.
**Rationale:** Standard floating-point types (`float`) cannot accurately represent base-10 monetary values, leading to precision drift during arithmetic operations. `Decimal` prevents this while natively supporting correct rounding. This representation is consistently used across `UserIntent`, `Cart`, `Mandates`, `ExecutionRequest`, and related entities.

## State Machine
The `TransactionState` manages the lifecycle of a VILR transaction explicitly. Allowed transitions are strictly enforced, and invalid transitions raise an `InvalidStateTransition` error.

**Success Path:**
`INTENT_RECEIVED` → `AP2_VERIFIED` → `CART_VERIFIED` → `RESERVATION_ACQUIRED` → `SEMANTIC_ANALYZED` → `POLICY_EVALUATED` → `AUTHORIZED` → `RESERVATION_COMMITTED` → `EXECUTION_STARTED` → `PAYMENT_CONFIRMED`

**Failure & Terminal States:**
- `PAYMENT_UNKNOWN`: Requires external reconciliation before moving to `PAYMENT_CONFIRMED` or `PAYMENT_FAILED`.
- Domain-specific failure terminals: `INVALID_SIGNATURE`, `HASH_MISMATCH`, `REPLAY_DETECTED`, `SEMANTIC_DRIFT`, `POLICY_DENIED`, `MANDATE_EXPIRED`, `MERCHANT_UNTRUSTED`, `DUPLICATE_EXECUTION`, `PAYMENT_FAILED`.

## Error Model
All errors derive from `VILRError`. The application maps these specific Python exceptions to appropriate HTTP responses in the FastAPI layer (e.g. `PolicyDenied` → 403 Forbidden).

## API Boundary
The API models (found in `app/api/schemas.py`) are strictly separated from domain models. Currently, in Phase 1, most API routes return a `501 Not Implemented` response except for `/health`.
