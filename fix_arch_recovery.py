with open("docs/architecture.md", "r") as f:
    text = f.read()

recovery_section = """
## 8. Revenue Recovery Extension Point
The current architecture safely isolates side effects, making it naturally compatible with a future **Revenue Recovery** layer without redesigning the core constraints.
- **`PAYMENT_FAILED` / `PAYMENT_UNKNOWN` Semantics**: If a transaction fails or times out, the `TransactionState` correctly tracks this. 
- **AI Recommendation**: In a future extension, an AI Agent could observe a `PAYMENT_FAILED` state and propose a recovery action (e.g., "retry with backup payment method pm-456").
- **Deterministic Authorization**: The recovery request would flow through the exact same OPA policy engine to ensure the backup method is allowed and the mandate hasn't expired.
- **Execution isolation**: Only the `PaymentExecutor` is permitted to initiate the retry, preserving the invariant that AI only *recommends* while the Gateway *authorizes and executes*.
"""

text = text + recovery_section
with open("docs/architecture.md", "w") as f:
    f.write(text)
