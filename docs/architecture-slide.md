# Architecture (Slide Version)

[Agent + Merchant] --(Signed Payload)--> [VILR Gateway]
                                              |-- Crypto Verification
                                              |-- AI Semantic (Evidence)
                                              |-- OPA (Authorization)
                                              |-- Redis (Idempotency)
                                              +-> [Payment Provider]
                                              +-> [Audit Ledger]
