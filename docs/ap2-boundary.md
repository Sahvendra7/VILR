# AP2 Protocol Boundary

VILR 2.0 acts as a runtime transaction-integrity gateway and an enforcement bridge for AP2-style transactions. It is a prototype and does not claim full conformance to the draft Agent Payments Protocol (AP2) specification.

## IMPLEMENTED / SIMPLIFIED
The following concepts are implemented but simplified for the prototype:
- **AP2-style mandate structures**: The data models (Open Checkout, Closed Checkout, etc.) conceptually mirror AP2 but use standard JSON fields.
- **ES256 Signatures**: Strict use of ECDSA P-256.
- **Hash Binding**: Open mandates and closed mandates are cryptographically linked via `checkout_hash` and `open_mandate_hash`.
- **Expiration Checks**: Strict `iat` and `exp` validation.

## NOT FULLY IMPLEMENTED
- **Full SD-JWT**: VILR uses standard JWTs. We do not implement Selective Disclosure JWTs (SD-JWT) for privacy-preserving claim redaction.
- **DID Infrastructure**: We use simple string identifiers (e.g., "user_123") instead of Decentralized Identifiers (DIDs) and DID resolution.
- **Production Key Distribution**: Keys are generated locally. There is no KMS integration or PKI certificate authority in this phase.
- **Real UPI Reserve Pay**: The execution phase uses a mocked Razorpay provider rather than a real banking network.
- **Production Merchant Registration**: Merchants are mock entities with hardcoded keys rather than participants in an active registry.

Do not claim full AP2 conformance. VILR is an evaluation of the *transaction integrity* concepts proposed by AP2.
