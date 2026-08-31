# Limitations

1. Mock payment provider (No real UPI/card rails integrated).
2. Simplified AP2-compatible representation (No full SD-JWT/DID ecosystem).
3. Local signer (No production KMS/HSM).
4. SQLite audit storage (Requires distributed immutable ledger in prod).
5. Probabilistic LLM (Cannot formally prove semantics).
6. Synthetic/adversarial benchmark (Needs real-world merchant data).
