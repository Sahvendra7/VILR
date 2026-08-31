# Baseline Comparison

| Baseline | Cart Tampering | Over Budget | Concurrent Replay | Semantic Sub | Result |
|----------|----------------|-------------|-------------------|--------------|--------|
| A: Unprotected Agent | Vulnerable | Vulnerable | Vulnerable | Vulnerable | Massive financial loss |
| B: Agent + Basic Policy | Vulnerable | Blocked | Vulnerable | Vulnerable | Agents manipulate cart |
| C: Crypto-only Gateway | Blocked | Blocked | Vulnerable | Vulnerable | Agent replays auth |
| **VILR Full Gateway** | **Blocked** | **Blocked** | **Blocked** | **Detected** | **Secure Execution** |

*Note: VILR's Semantic Verification is probabilistic; Crypto, Idempotency, and OPA are deterministic.*
