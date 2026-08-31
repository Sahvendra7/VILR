# Production Roadmap

- **Local signer -> KMS/HSM:** Move private key handling to AWS KMS or HashiCorp Vault.
- **SQLite -> PostgreSQL/QLDB:** Move the audit chain to a horizontally scalable, cryptographically verifiable database (like AWS QLDB).
- **Mock payment -> Razorpay APIs:** Implement the `PaymentProvider` interface using Razorpay's Server-to-Server SDK.
- **Prototype semantic model -> evaluated production model:** Rigorous offline evaluation dataset curation.
- **Local Redis -> Redis Enterprise:** Ensure highly available, multi-AZ idempotency.
- **Simplified AP2 -> Full Protocol Conformance:** Implement exact SD-JWT selective disclosure.
