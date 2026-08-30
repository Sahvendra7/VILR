# VILR Cryptography Architecture

This document describes the cryptographic primitives, structures, and trust relationships employed by VILR.

## Algorithm Choices
- **Signature Algorithm**: ECDSA P-256 (secp256r1) with SHA-256. This is enforced exclusively (ES256). Ed25519 and RSA are explicitly rejected to comply with hardware security module (HSM) requirements defined in the broader AP2 spec.
- **Hash Algorithm**: SHA-256.
- **Canonicalization**: RFC 8785 JSON Canonicalization Scheme (JCS) ensures deterministic hashing of JSON structures regardless of key ordering or whitespace.

## Key Roles & Trust Relationships
The system recognizes three distinct signer roles:
1. **USER**: Signs Open Checkout Mandates, binding their intent and budget constraints to an agent.
2. **AGENT**: Not currently a signer in Phase 2, but structurally distinct. In full AP2 they may co-sign or hold delegation tokens.
3. **MERCHANT**: Signs Closed Checkout Mandates (Merchant Offers), binding a specific cart and price to the User's open mandate.

VILR strictly verifies that a mandate claiming to be from a Merchant was actually signed by the Merchant's key. Mismatched signer identities result in `InvalidSignature`.

## Data Structures

### JWK Representation
Public keys are represented as JSON Web Keys (JWK) containing the EC parameters:
- `kty`: "EC"
- `crv`: "P-256"
- `x`, `y`: Base64URL encoded coordinates.

### JWT Structure
Mandates are standard ES256 JWTs. They include mandatory claims: `iss` (Issuer), `sub` (Subject), `iat` (Issued At), `exp` (Expiration). VILR strictly enforces time bounds.

### JCS & Hashing
- `compute_jcs_hash`: Produces a deterministic Base64URL-encoded SHA-256 digest of an RFC 8785 canonicalized JSON payload.
- `checkout_hash`: Hashing the Cart properties (merchant_id, currency, total_amount, items). Any mutation to these fields fundamentally alters the hash, preventing cart tampering (e.g., price drops or quantity increases).
- `open_mandate_hash`: The hash of the open mandate's integrity-bound fields. The Closed Checkout Mandate includes this hash (`open_mandate_ref`) to cryptographically bind the merchant's offer to the user's explicit authorization.

## What Cryptography Proves
- **Integrity**: The cart and intent have not been modified since signing.
- **Authentication**: The payload was signed by the holder of the specific private key.
- **Expiration**: The mandate was created and evaluated within acceptable time bounds.

## What Cryptography Does NOT Prove
- **Authorization**: Cryptography proves *who* signed *what*, but OPA determines if that action is allowed under the current business rules (budget limits, etc.).
- **Delegation/Legal Liability**: The prototype does not resolve legal disputes or implement complex chain-of-trust PKI. It validates the technical boundary.
