# VILR Demo Script

This script outlines the flow for demonstrating the VILR project to evaluators.
Run the deterministic demo using: `python -m scripts.cli demo`

## 1. Introduction
"Welcome. We are demonstrating VILR, a payment orchestration layer that bridges deterministic financial controls with non-deterministic agentic actions. We assume the identity (AP2) is already verified, and focus on preventing unauthorized financial side-effects."

## 2. Standard Flows
- **Scenario 1: Valid Purchase**
  - Show a standard transaction passing Cryptography, Semantic AI, and OPA, then executing successfully.
- **Scenario 2: Semantic Substitution**
  - Show an agent attempting to buy a gaming laptop when authorized for office supplies. The LLM correctly identifies the mismatch and blocks it.
- **Scenario 3: Cart Tampering**
  - Show a payload where the amount is tampered from 500 to 9999. The cryptographic hash fails instantly.

## 3. Hero Demonstrations
- **Scenario 6: The Concurrency Test**
  - "Here we send 100 identical execution requests simultaneously to simulate a race condition."
  - Output shows 1 ALLOW and 99 DENY.
  - "The Payment Provider was called exactly 1 time. Redis Lua scripts guarantee atomic token consumption."
- **Scenario 7: Network Timeout Reconciliation**
  - "What happens when the provider times out?"
  - Output shows `PAYMENT_UNKNOWN`.
  - "We do not retry. We fail-closed and leave the transaction in a state pending asynchronous reconciliation."
- **Scenario 8: Audit Tampering**
  - "We mutate the in-memory audit ledger and run the verifier."
  - Output shows the hash chain breaking, exposing the tampering.

## 4. Benchmark Results
- Run: `python -m scripts.cli security`
- Highlight the 40 adversarial tests.
- Point to the final Unauthorized Payment Execution Rate: 0%.
- "VILR successfully contained all side-effects across prompt injections, replays, concurrent attacks, and policy bypasses."
