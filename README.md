# VILR: Verifiable Intent & Liability Runtime

## PROBLEM:
AI agents introduce a new payment trust boundary. They can hallucinate, and merchants can inject malicious prompts, making autonomous AI payments extremely dangerous if the AI has the authority to move money.

## SOLUTION:
VILR separates probabilistic AI interpretation from deterministic payment authorization. It uses a zero-trust cryptographic gateway to authorize the actual financial execution.

## CORE PRINCIPLE:
"AI can interpret and recommend. AI cannot authorize money movement."

## ARCHITECTURE:
Gemini → Crypto → OPA → Redis → PaymentExecutor → Razorpay → Supabase

## 1. Quickstart
```bash
# Clone and setup
git clone https://github.com/sahvendraz/VILR.git
cd VILR
python3 -m venv venv && source venv/bin/activate
pip install -e .
```

## 2. Safe Demo
```bash
# Run the live, safe demo with real infrastructure (no production funds)
python scripts/cli.py demo --llm gemini --provider mock --ledger supabase
```

## 3. Live Integrations
- **Gemini 3.1 Flash-Lite**: Semantic Verification.
- **Razorpay TEST**: Controlled test-mode execution.
- **Supabase**: Persistent tamper-evident audit chain.
- **Redis Lua**: Atomic idempotency locking.
- **OPA**: Deterministic authorization.

## 4. Security Evidence
In our rigorous security benchmark testing (40 attack vectors covering cart tampering, replay attacks, concurrent double-spends, and semantic manipulation):
- **0 unauthorized payments were executed.**
- 16 attacks were deterministically blocked by Gateway layers (Crypto, Redis, OPA).
- Semantic mismatch and prompt injections were consistently mitigated without overriding OPA budgets.

## 7. Gemini Integration
VILR integrates the official `google-genai` SDK using `gemini-3.6-flash`. It utilizes strict structured outputs (JSON schema) and securely fails closed on timeouts or schema violations. Gemini acts as an independent semantic assessor (evidence provider), remaining strictly subordinate to OPA.

## 8. Limitations & Scope
- **Prototype Status**: VILR is a Razorpay Buildathon prototype.
- **Mock Razorpay**: Currently executes against a simulated Razorpay TEST payment executor.
- **AP2-Compatible**: The cryptography simulates the Advanced Payments 2.0 (AP2) specification concepts but is a lightweight representation, not a compliant implementation.
- **Simulated Recovery**: The revenue recovery metrics shown in the demo are conceptually simulated to demonstrate potential ROI.

For detailed architecture, security models, and performance benchmarks, see the `docs/` directory.

## Tier 1 Security Enhancements
- **Exception Intelligence**: Advisory/explanatory only. LLM has no authorization authority.
- **Security Receipt**: Deterministic evidence generated from actual system state.
- **Ground-Truth Evaluation**: Expected decision vs actual decision + expected side effect vs actual side effect.
- **Supabase**: Persistent tamper-evident audit storage.
