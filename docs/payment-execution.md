# Payment Execution Layer (Phase 6)

## PaymentProvider Interface
The `PaymentProvider` protocol defines the boundary between the VILR Gateway and the final payment execution environment (e.g., Razorpay UPI Reserve Pay).
It exclusively models the financial side effect without making any authorization or policy decisions.

## PaymentExecutor
The `PaymentExecutor` is responsible for orchestrating the execution flow:
1. Validates that the transaction has successfully acquired and committed a reservation (`RESERVATION_COMMITTED` state).
2. Prevents unauthorized execution attempts.
3. Transitions state to `EXECUTION_STARTED`.
4. Dispatches the `ExecutionRequest` to the `PaymentProvider`.
5. Maps the provider's result to standard terminal states (`PAYMENT_CONFIRMED`, `PAYMENT_FAILED`, `PAYMENT_UNKNOWN`).

## Provider Idempotency vs Gateway Reservation
It is critical to distinguish between gateway reservation and provider-side idempotency:
- **Gateway Reservation (Redis):** Checks "Can this authorization reserve execution?" before hitting the provider, preventing concurrent logic races inside VILR.
- **Provider-Side Idempotency:** The provider ensures that a single `idempotency_key` maps to one and only one logical payment operation.
- **Fingerprinting:** The idempotency key is paired with a canonical SHA-256 fingerprint of the request (`amount`, `currency`, `merchant_id`, `mandate_hash`). If the same key is reused with different parameters, the provider rejects it as an `IdempotencyConflict`.

## Duplicate Handling
If the `PaymentExecutor` calls the provider with the same `idempotency_key` and matching request parameters, the provider does NOT create a new payment. Instead, it replays the original deterministic outcome.

## The UNKNOWN State
`PAYMENT_UNKNOWN` means: **"The payment outcome is unknown to VILR."**
It does NOT mean "The payment failed." This typically occurs if the provider simulates a network timeout *after* accepting the request.
- The state machine enters `PAYMENT_UNKNOWN`.
- VILR does NOT automatically retry (which could cause a double debit).
- A separate reconciliation process must be triggered.

## Reconciliation Model
Reconciliation transitions an ambiguous state to a confirmed state.
The `PaymentExecutor` exposes a `reconcile()` method that invokes `get_payment_status()` on the provider.
- `PAYMENT_UNKNOWN -> PAYMENT_CONFIRMED`
- `PAYMENT_UNKNOWN -> PAYMENT_FAILED`

## Payment Failure
A confirmed failure from the provider (e.g., `INSUFFICIENT_FUNDS`) is terminal. The state becomes `PAYMENT_FAILED`, and no automatic retries are performed by the execution layer.

## Execution Boundaries & Mock Limitations
- The current `MockRazorpayProvider` simulates execution using a simple in-memory dictionary and `asyncio.Lock()`.
- It does not persist across application restarts.
- It is a simulation for testing the VILR security boundary; it is not the Razorpay TEST/Sandbox API.
- The `PaymentExecutor` is deliberately decoupled from the gateway orchestrator (Phase 7). The orchestration layer must securely bind the AP2 verification pipeline to the executor.
