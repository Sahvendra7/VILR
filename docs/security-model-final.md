# Final Security Model

### Semantic Layer
- **Threat:** Intent drift or prompt injection.
- **Control:** LLM semantic verifier with strict input bounds.
- **Guarantee:** Probabilistic detection.
- **Limitation:** Not deterministic; assumes OPA fallback for hard rules.

### Cryptographic Layer
- **Threat:** Cart tampering by merchant or agent.
- **Control:** JCS Canonicalization + ECDSA P-256 JWTs.
- **Guarantee:** Deterministic tamper evidence.
- **Limitation:** Requires secure key distribution.

### Idempotency Layer
- **Threat:** Accidental or malicious replay (concurrency).
- **Control:** Redis atomic Lua scripts.
- **Guarantee:** At-most-once authorization pass-through.
- **Limitation:** Network availability.

### OPA Policy Layer
- **Threat:** Financial policy bypass.
- **Control:** Default-deny Rego policies.
- **Guarantee:** Deterministic hard constraints (budget, merchant).
- **Limitation:** Depends strictly on accurate inputs.
