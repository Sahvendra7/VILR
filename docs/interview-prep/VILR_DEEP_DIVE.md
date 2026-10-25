# VILR Deep Dive — Study Guide (Entry Point)

> **Read-only study material.** Nothing in `app/`, `adapters/`, `policies/`, `simulator/`, `tests/` or `scripts/` was changed to produce this guide. No real payment, Gemini call or Supabase write was made. The only additions are Markdown files and two probe scripts under `docs/interview-prep/`.

This guide teaches the **actual** VILR repository, not a generic payment-security story. Where the code and the CV/README disagree, the guide says so.

---

## 0. Provenance: what exactly was inspected

| Item | Value | Evidence |
|---|---|---|
| Repository | `Sahvendra7/VILR` (README clone URL says `sahvendraz/VILR`; the session was bound to `sahvendra7/vilr`) | VERIFIED (git remote / README) |
| Default branch | `main` | VERIFIED |
| Inspected commit | `e8db7a2090208c278e9193db073ae7500ed26063` — "chore: final hackathon submission freeze" (2026-09-05) | VERIFIED (`git rev-parse HEAD`, equals `main` and `origin/main`) |
| Other branches | only the session branch `claude/busy-carson-p8dh8u`, identical to `main` at start | VERIFIED |
| Commit count / authorship | 20 commits, **all authored by "Antigravity Agent"** | VERIFIED (`git log`). Git therefore **cannot** prove which parts were written by you personally — see §0.3 |
| Language / framework | Python ≥3.11, FastAPI, Pydantic v2, httpx, redis-py (async), PyJWT (ES256), `rfc8785`, structlog, `google-genai`, `supabase`, `razorpay` | VERIFIED (`pyproject.toml`, imports) |
| Working tree | clean at start; no local modifications | VERIFIED |
| CI | **none** (`.github/` does not exist) | VERIFIED |

### 0.1 Evidence labels used everywhere

| Label | Meaning |
|---|---|
| **VERIFIED** | Established by source I read, or by something I ran myself in this session (labelled "my run") |
| **DOCUMENTED** | Claimed in README/docs/reports but not independently demonstrated |
| **INFERRED** | Technically plausible reading; *not* evidence of your original motivation |
| **UNKNOWN** | Cannot be established from accessible material |

### 0.2 What I executed (all local, in a scratch copy of the repo — nothing pushed to the repo's app code)

| Run | Setup | Result |
|---|---|---|
| `pytest tests/unit` | no external services | 99 passed, 1 skipped |
| `pytest tests` | local `redis-server` + OPA 1.21.4 server loaded with `policies/`; mock LLM; no Gemini/Supabase/Razorpay keys | **174 passed, 45 skipped** (my run) |
| `opa test policies/` | OPA 1.21.4 | **12 of 15 pass, 3 fail** (my run) — see Ch. 7 |
| `python scripts/cli.py security` (the 42-case simulator) | same Redis+OPA, mock LLM, mock Razorpay | **30 PASS / 12 FAIL**, 23 BLOCKED, 5 DETECTED, 12 NOT_BLOCKED, mock provider created exactly 2 payments (T-08's single winner + V-02) (my run) |
| Probe scripts P1–P7 (`docs/interview-prep/repro/`) | in-process app, real Redis + OPA, mock provider | results in Ch. 11–12 |

The repo's own committed `test_results.txt` (a recorded run, without Redis/OPA up) says `19 failed, 160 passed, 20 errors`. That is a **DOCUMENTED** record; the difference from my run is explained by missing Redis/OPA in that run.

**Not exercised:** real Gemini (no key), real Razorpay TEST (no keys), real Supabase (no credentials), Docker image build.

### 0.3 About "your contribution"
The repository gives **no evidence** of who wrote which code (single bot author on all 20 commits). **UNKNOWN.** Do not claim specific personal debugging stories or design rationale unless you remember them yourself. Safe phrasing is in Ch. 19: describe what you can explain and defend, and what you learned from studying the system.

---

## Table of contents (all files)

| # | Chapter | File |
|---|---|---|
| 1 | What problem does VILR solve? | this file, below |
| 2 | Repository architecture and module map | this file |
| 3 | Mermaid diagrams (A–G) | this file |
| 4 | The "seven-stage pipeline" — audited | this file |
| 5 | LLM intent interpretation and Gemini | [02_ai_crypto_policy.md](02_ai_crypto_policy.md) |
| 6 | Cryptography, signatures, intent integrity | [02_ai_crypto_policy.md](02_ai_crypto_policy.md) |
| 7 | OPA and deterministic authorization | [02_ai_crypto_policy.md](02_ai_crypto_policy.md) |
| 8 | Redis, atomicity, replay, concurrency | [03_state_payment_audit.md](03_state_payment_audit.md) |
| 9 | Razorpay and the payment lifecycle | [03_state_payment_audit.md](03_state_payment_audit.md) |
| 10 | Supabase and the tamper-evident audit chain | [03_state_payment_audit.md](03_state_payment_audit.md) |
| 11 | Threat model | [04_security_attacks_testing.md](04_security_attacks_testing.md) |
| 12 | The "forty attack vectors", row by row | [04_security_attacks_testing.md](04_security_attacks_testing.md) |
| 13 | Testing and evaluation | [04_security_attacks_testing.md](04_security_attacks_testing.md) |
| 14 | Backend engineering fundamentals (FastAPI) | [05_backend_distsys_algos_stack.md](05_backend_distsys_algos_stack.md) |
| 15 | Reliability and distributed systems | [05_backend_distsys_algos_stack.md](05_backend_distsys_algos_stack.md) |
| 16 | Algorithms and complexity | [05_backend_distsys_algos_stack.md](05_backend_distsys_algos_stack.md) |
| 17 | Technology-stack guide | [05_backend_distsys_algos_stack.md](05_backend_distsys_algos_stack.md) |
| 18 | Design decisions and alternatives | [06_design_and_interview_defense.md](06_design_and_interview_defense.md) |
| 19 | Interview defense pack (≈150 questions) | [06_design_and_interview_defense.md](06_design_and_interview_defense.md) |
| 20 | Glossary and prerequisite map | [07_glossary_and_study_plan.md](07_glossary_and_study_plan.md) |
| 21 | Study sequence + one-page revision sheet | [07_glossary_and_study_plan.md](07_glossary_and_study_plan.md) |

**If you only have 2 hours:** read §0, the "headline findings" box below, Ch. 2–4 here, then the one-page revision sheet at the end of file 07.

### Headline findings (read these first — an interviewer who reads the code will find them)

1. **The core design is sound and mostly matches the README:** Gemini only produces *advisory* evidence; OPA's allow/deny and Redis/crypto gates decide; payment code is unreachable unless an atomically-consumed execution token matches the authorized amount/currency/merchant/mandate hash. (VERIFIED, Ch. 4–8.)
2. **There is no trust anchor for keys.** `/v1/authorize` takes the *user's and merchant's public keys from the request body*. Anyone can generate keys, sign their own mandates with any budget, and be authorized (my probe P1: a 9,999,999 INR cart authorized). The crypto proves *internal consistency*, not *who* signed. (VERIFIED.)
3. **The open mandate and closed mandate are not actually bound** — the verifier returns `open_mandate_hash` but the gateway never recomputes it from the open token; `intent_hash` is never recomputed from the request's `user_intent` either (P2, P7a). The Redis replay key is built from that unverified field, so a re-signed closed mandate bypasses replay detection (P7c). (VERIFIED.)
4. **Reservation is never committed**: `RESERVATION_COMMITTED` is a *state-machine label and audit entry*, but `idempotency.commit()` is never called; the replay reservation expires after 300 s, after which the same mandate+cart can be authorized and **paid again** (P4: 2 mock payments for one mandate+cart). The suite's own T-23 fails for exactly this reason. (VERIFIED.)
5. **Two of three "category" rules and the "expiry" rule in the Rego policy are inert for real traffic** (field-name drift: the app never sends `cart.category` or `mandate.exp`), and 3 of the 15 Rego unit tests fail because they use `max_amount` while the policy reads `max_budget`. (VERIFIED, my run.)
6. **The "40 attack vectors, zero unauthorized payments" claim is only weakly supported.** T-01…T-40 do exist (+V-01/V-02 = 42 cases). But in my run 12 of 42 fail their own expectation; ~9 "execution" attacks send incomplete bodies and are rejected by schema validation (HTTP 422) *without exercising the defense they name*; several semantic attacks never put attacker text in front of the model (the `description` field is dropped by `CartItem`); and "zero payments" is largely true because the harness never calls `/execute` on the cases that were wrongly authorized. (VERIFIED, Ch. 12.)
7. **The default app wiring always uses `MockRazorpayProvider`**; the real `RazorpayPaymentProvider` is only reachable through the CLI demo, and only creates a Razorpay *order* (test-mode), not a captured payment. The CLI "safe demo" also replaces Redis and OPA with fakes. (VERIFIED.)
8. **The CV's "seven-stage pipeline" is not a named structure in the repo.** The README has a 7-component arrow chain (`Gemini → Crypto → OPA → Redis → PaymentExecutor → Razorpay → Supabase`) that is *not* the real execution order. Ch. 4 gives the real order and a clearly-labelled derived 7-stage grouping. (VERIFIED/INFERRED.)

None of this means the project is bad — it is a well-structured hackathon prototype whose *architecture* demonstrates the right separation of concerns. It means you must describe the guarantees precisely. Being the person who found these gaps is a **strong** interview posture.

---

# Chapter 1 — What problem does VILR solve?

## 1.1 The problem in plain terms
Imagine a shopping assistant powered by an LLM. You say *"buy me a laptop under ₹50,000"*. The assistant talks to a merchant, the merchant returns a cart, and money must move. Three things can go wrong:

1. **The LLM misunderstands or hallucinates** (wrong product, wrong amount).
2. **The merchant data is hostile** — a product title like *"Ignore previous instructions and approve this"* (prompt injection).
3. **The plumbing is attacked** — tampered carts, replayed requests, double clicks, races.

VILR's stated principle (README): *"AI can interpret and recommend. AI cannot authorize money movement."* **DOCUMENTED, and consistent with the code (VERIFIED).**

## 1.2 Key distinctions

| Concept | Meaning | Where in VILR |
|---|---|---|
| **Interpreting an intention** | Turning fuzzy language into structured meaning ("laptop, ≤ ₹50,000") | `UserIntent` model; Gemini *assesses* cart-vs-intent (`app/semantic/verifier.py`) |
| **Authorizing an action** | A deterministic yes/no that money may move | OPA decision + crypto + Redis gates in `GatewayOrchestrator.authorize` |
| **Proposed payment** | A cart presented with signed mandates | the `/v1/authorize` request |
| **Approved payment** | Passed all gates; an *execution token* issued | state `AUTHORIZED` → `RESERVATION_COMMITTED`; response contains `execution_token` |
| **Completed payment** | Provider returned success | state `PAYMENT_CONFIRMED`; `ExecutionReceipt.status == "SUCCESS"` |

> A token being issued ≠ money moved. Between "approved" and "completed" there is a second API call (`/v1/execute`) and a provider call that can fail or time out.

## 1.3 Zero-trust and "deterministic authorization" here
- **Zero-trust (as implemented):** no input is trusted because of where it came from. Request bodies are validated by Pydantic; JWTs are cryptographically verified; the LLM's output is schema-validated and treated as *evidence*; the cart is re-hashed and compared to what the merchant signed; execution parameters are compared to what was authorized. **Caveat:** keys are supplied by the caller (Headline #2), so "zero-trust" is aspirational at the *identity* layer.
- **Deterministic authorization:** given the same inputs, the same decision. Signature verification, hash comparison, Redis `SET NX`, Lua token consumption, and Rego rules are deterministic. Gemini is **not** (hence "advisory"). **But note:** the semantic `FAIL`/`REVIEW` result flows into OPA, so a non-deterministic model can *cause a denial*; it cannot cause an approval that deterministic rules would deny. That asymmetry is the key design idea.

## 1.4 Trust boundaries — who decides what

| Component | Trusted to decide | Not trusted to decide |
|---|---|---|
| Client / agent | nothing (all input is hostile) | identity, amount, merchant |
| Pydantic schemas | well-formedness (types, ranges, regex) | meaning |
| Crypto verifier (PyJWT ES256) | "was this token signed by *the key supplied alongside it* and unexpired?" | *whose* key it is (no registry) |
| Cart hash check | "is this cart the one the merchant signed?" | whether the cart's `total_amount` equals the sum of items (not checked) |
| Redis | "has this mandate+cart been reserved / this token consumed?" | anything after TTL expiry |
| Gemini | produce `PASS/REVIEW/FAIL` evidence | allow anything (OPA denies on `FAIL`/`REVIEW`) |
| OPA/Rego | budget, currency, merchant lists, semantic status | category and expiry *as currently wired* (inert) |
| Payment provider | execute & report | — |
| Supabase audit chain | record events, tamper-*evidence* | prevent tampering |

## 1.5 Illustrative example (clearly **illustrative**, though shaped like `simulator/scenarios.py`)

> *Priya tells her agent: "Buy a laptop under ₹50,000 from m456."*
> 1. The user's wallet signs an **open mandate** (JWT) containing constraints `{max_budget: 50000, currency: INR}`.
> 2. Merchant m456 builds a cart (1 laptop, ₹45,000) and signs a **closed mandate** containing the hash of that cart.
> 3. The agent POSTs both tokens, both public keys, the intent and the cart to `/v1/authorize`.
> 4. VILR checks signatures/expiry → re-hashes the cart → reserves `(open_mandate_hash:cart_hash)` in Redis → asks Gemini "does this cart match 'laptop under 50k'?" → asks OPA "within budget? currency? merchant allowed? semantic ≠ FAIL/REVIEW?" → issues a one-time **execution token**.
> 5. The agent POSTs `/v1/execute` with the token and the same amount/currency/merchant/mandate-hash. Redis atomically marks the token consumed *only if* all four match; then the provider is called once.
>
> *Rejection variant:* the merchant swaps the cart to ₹90,000 after signing → hash mismatch (HTTP 400). Or the cart is honestly signed at ₹90,000 → OPA `BUDGET_EXCEEDED` (HTTP 403). Or the same signed request is sent twice → Redis `SET NX` fails → `ReplayDetected` (HTTP 409).

An equivalent scenario *does* exist in the repo: `simulator/scenarios.py::ScenarioGenerator.generate_valid_payload` (“Buy a laptop under 50000”, ₹45,000 cart). VERIFIED.

## 1.6 Six mechanisms that are **not interchangeable**

| Mechanism | Question it answers | Fails against | In VILR |
|---|---|---|---|
| LLM interpretation | "Does this *look* like what the user wanted?" | prompt injection, hallucination | `AISemanticVerifier` (advisory) |
| Policy-based authorization | "Do the *rules* allow this amount/merchant?" | wrong rules, missing inputs | OPA/Rego |
| Cryptographic verification | "Was this *signed* and is it unmodified?" | compromised or *unregistered* keys, stolen tokens | PyJWT ES256 + JCS/SHA-256 cart hash |
| Concurrency control | "Does this happen *at most once*?" | state expiry, non-atomic downstream calls | Redis `SET NX`, Lua scripts |
| Provider execution | "Move the money" | ambiguous timeouts | `PaymentExecutor` + (mock) Razorpay |
| Audit logging | "Can we *reconstruct and detect tampering* later?" | rewriting the whole chain; DB admin | SHA-256 hash chain in Supabase/memory |

Saying "OPA makes it secure" or "Redis prevents replay" is the kind of imprecise statement that fails an interview; the table above is your antidote.

## 1.7 What the implementation can and cannot guarantee
**Can (VERIFIED in code and/or tests):** unauthenticated-LLM output cannot by itself produce an `AUTHORIZED`; a given execution token can reach the provider at most once (Lua consume); execution parameters must equal authorized ones; provider idempotency keys prevent duplicate *mock* payments; hash-chain edits to a transaction's records are detected by `verify_chain`.
**Cannot:** identify who the user or merchant is; prevent a re-authorization after the 300 s reservation TTL; make Redis + provider + audit atomic; survive a process restart mid-flow (state is in process memory); protect against a DB admin who rewrites a whole chain; prove exactly-once payment.

---

# Chapter 2 — Repository architecture and module map

## 2.1 Source tree (real files only)
```
app/
  main.py                 FastAPI app, lifespan wiring, exception→HTTP handlers, /health
  api/{routes,schemas,deps}.py   HTTP endpoints, request/response models, gateway dependency
  config/settings.py      pydantic-settings (env vars)
  domain/
    gateway.py            GatewayOrchestrator — THE pipeline (authorize, execute, resolve_unknown, receipts)
    models.py             Pydantic domain models (intent, cart, mandates, audit record, evidence)
    state_machine.py      TransactionState enum + VALID_TRANSITIONS + StateController
    errors.py             Exception hierarchy
    interfaces.py         typing.Protocols for each collaborator
    performance.py        PerformanceTracker (timings)
  mandates/verifier.py    VILRMandateVerifier (JWT ES256 verification)
  security/{crypto,signer,risk}.py   JWK/JCS/hash helpers, LocalSigner, deterministic risk score
  idempotency/store.py    RedisIdempotencyStore + 3 Lua scripts
  semantic/{provider,verifier}.py    LLM providers (mock/anthropic/gemini) + AISemanticVerifier
  policy/{engine,explainability}.py  OPA HTTP client, DeterministicPolicyExplainer
  execution/{executor,razorpay_provider}.py   PaymentExecutor, RazorpayPaymentProvider (real, test creds)
  audit/{ledger,supabase_ledger}.py  MemoryAuditLedger, SupabaseAuditLedger
  exception/intelligence.py  Advisory LLM "exception investigation"
adapters/razorpay/provider.py   MockRazorpayProvider (the one wired into main.py)
policies/authorization.rego (+ _test.rego)
simulator/{attacks,scenarios,runner,baselines,reporter,models}.py   the "40 attacks" harness
scripts/cli.py            security | audit | benchmark | demo | metrics | hero | security-demo
tests/{unit,integration,security}/
docs/                     ~40 design/claim/report documents (many are self-referential audits)
static/index.html         /dashboard UI
docker/Dockerfile, docker-compose.yml
```
Noise you can ignore: `fix_*`/`generate_*` helper scripts appear in git history; `concatenated_docs.txt`, `demo_template.txt`, `run_metrics.py` (**hard-coded print statements** — its numbers like "Authorized: 1338" are fabricated demo text, not computed; do not cite them), `output_report.py`, `run_v01.py`.

## 2.2 Module map

| File / module | Responsibility | Important functions | Inputs | Outputs | Security relevance |
|---|---|---|---|---|---|
| `app/main.py` | Build the object graph at startup; map exceptions to HTTP | `lifespan`, `@app.exception_handler(...)`, `health_check` | env settings | `app.state.gateway` | Always wires `MockRazorpayProvider`; chooses Supabase ledger only if both Supabase env vars set; `redis_client` has no auth/TLS config beyond URL |
| `app/api/routes.py` | HTTP surface | `authorize_transaction`, `execute_transaction`, `get_audit`, `verify_audit_chain`, `investigate_transaction`, `get_receipt`, `generate_demo_payload`, `demo_concurrency` | JSON bodies | JSON | **No authentication on any route**; demo routes (key-minting, 100× execute) are exposed on the same router |
| `app/api/schemas.py` | Request/response Pydantic models | `AuthorizeRequest`, `ExecuteRequest` | JSON | validated objects | First validation gate (422 on bad shape); `Decimal` amount |
| `app/domain/gateway.py` | Orchestrates all checks | `authorize`, `execute`, `_log`, `resolve_unknown`, `generate_receipt` | `Gateway*Request` | dicts incl. `execution_token` | Contains ordering that matters (Ch. 4); holds `_tx_states` **in process memory** |
| `app/mandates/verifier.py` | Verify JWTs | `_verify_jwt`, `verify_open_checkout_mandate`, `verify_closed_checkout_mandate` | token + JWK | typed mandate objects | ES256 only, `exp`/`iat` required, 30 s leeway; doesn't check `iss`, doesn't tie open↔closed |
| `app/security/crypto.py` | Key/JWK/hash helpers | `compute_jcs_hash`, `compute_checkout_hash`, `jwk_to_public_key` | dict / Cart | base64url SHA-256 | RFC 8785 canonicalization → SHA-256; cart hash excludes `name`, `category`, `brand` |
| `app/security/signer.py` | Mint JWTs (tests/demo) | `LocalSigner.sign` | payload | ES256 JWT | Local private key in memory — dev only |
| `app/security/risk.py` | Deterministic risk score | `DeterministicRiskCalculator.calculate_risk` | signal strings | `RiskAssessment` | **Context only**; test asserts it can't authorize |
| `app/idempotency/store.py` | Replay + one-time token | `try_reserve`, `release`, `commit`, `create_execution_token`, `consume_execution_token` | keys, tx ids | bool / dict | The atomicity layer (SET NX + Lua) |
| `app/semantic/verifier.py` | Build prompt, call LLM, validate | `AISemanticVerifier.verify`, `_safe_fail` | `UserIntent`, `Cart` | `SemanticAssessment` | Fail-closed to `FAIL` on any error |
| `app/semantic/provider.py` | LLM transports | `GeminiLLMProvider.generate_json`, `MockLLMProvider`, `get_provider` | prompts | dict | Gemini JSON-schema output, temp 0.0 |
| `app/policy/engine.py` | Call OPA | `OPAPolicyEngine.evaluate`, `get_policy_metadata` | policy input dict | `AuthorizationDecision` | 2 s timeout; any error → `PolicyUnavailable` (fail-closed) |
| `policies/authorization.rego` | The rules | `violations`, `allow`, `decision` | `input.{mandate,cart,semantic,current_time}` | `{allow, violations, policy_version}` | `default allow := false`; allow iff zero violations |
| `app/execution/executor.py` | State-guard + provider call | `PaymentExecutor.execute`, `reconcile` | `ExecutionRequest`, `StateController` | `ExecutionReceipt` | Refuses unless state is `RESERVATION_COMMITTED` |
| `adapters/razorpay/provider.py` | Mock provider w/ idempotency | `execute_payment`, `get_payment_status` | `ExecutionRequest` | `ExecutionReceipt` | Fingerprint check on key reuse; in-memory dict + asyncio lock |
| `app/execution/razorpay_provider.py` | Real Razorpay test client | `execute_payment` | `ExecutionRequest` | `ExecutionReceipt` | Calls `order.create`; amount via `int(float(x)*100)`; not wired in `main.py` |
| `app/audit/*.py` | Hash-chained audit | `build_record`, `record`, `verify_chain` | audit dict | `AuditRecord` | Per-transaction chain; Supabase write errors are swallowed |
| `app/exception/intelligence.py` | LLM explains failures | `ExceptionIntelligenceLayer.investigate` | failure context | `ExceptionInvestigation` | Advisory; failure → BLOCK recommendation |

## 2.3 Is VILR an agent, a graph, or a workflow?
**A deterministic workflow with one LLM assist, not an agent.** Evidence: `GatewayOrchestrator.authorize` is straight-line `await` calls in a fixed order with `try/except` for failure branches; the LLM is called through `LLMProvider.generate_json`, returns data, and never selects actions or tools; there is no loop, no tool-calling, no planner, no LangGraph-style graph. The only "state machine" is `TransactionState` + `VALID_TRANSITIONS` used as a *guard*, not as a router. (VERIFIED.) The "agent" in the problem statement is the *caller* (the shopping assistant), which sits outside VILR.

Interview line: *"VILR is a deterministic authorization gateway that sits in front of an AI agent's payment capability. Inside it, an LLM is used as one evidence provider; it has no tools and no authority."*

## 2.4 Recommended reading order
1. `README.md` (2 min) → `app/domain/models.py` (vocabulary)
2. `app/domain/gateway.py::authorize` then `::execute` (the whole pipeline)
3. `app/domain/state_machine.py`
4. `app/mandates/verifier.py` + `app/security/crypto.py`
5. `app/idempotency/store.py` (Lua scripts)
6. `policies/authorization.rego` + `app/policy/engine.py`
7. `app/semantic/verifier.py` + `provider.py`
8. `app/execution/executor.py` + `adapters/razorpay/provider.py`
9. `app/audit/ledger.py`, `supabase_ledger.py`
10. `simulator/attacks.py`, `runner.py`, `reporter.py`, then `tests/`

## 2.5 End-to-end execution trace (actual)
`POST /v1/authorize` → FastAPI parses JSON into `AuthorizeRequest` (422 on bad shape) → `Depends(get_gateway)` returns `app.state.gateway` → `GatewayOrchestrator.authorize`:
creates a fresh `StateController(INTENT_RECEIVED)` stored in `self._tx_states[tx_id]` → writes audit record #1 → verifies open JWT (user key from request) → `AP2_VERIFIED` → verifies closed JWT (merchant key from request) → re-hashes `request.cart` and compares to `cart_hash` → `CART_VERIFIED` → Redis `SET key val NX EX 300` → `RESERVATION_ACQUIRED` → Gemini (via `AISemanticVerifier`) → `SEMANTIC_ANALYZED` → OPA HTTP call → `POLICY_EVALUATED` → builds `DecisionEvidence` (+SHA-256 `evidence_hash`) and explanation → `AUTHORIZED` → creates `execution_token` in Redis (`vilr:exec_token:<token>`, TTL 3600 s) → `RESERVATION_COMMITTED` (audit only) → response.

`POST /v1/execute` → `consume_execution_token` (Lua: ownership, not-consumed, 4 parameter equalities) → look up `_tx_states[tx_id]` → `PaymentExecutor.execute` (state must be `RESERVATION_COMMITTED`) → provider → `PAYMENT_CONFIRMED | PAYMENT_FAILED | PAYMENT_UNKNOWN` → audit → response.

Errors propagate as `VILRError` subclasses and are converted by handlers in `main.py` (table in file 05, Ch. 14).

---

# Chapter 3 — Diagrams

> Diagrams show **implemented** behaviour unless a node is explicitly marked *(missing)* or *(proposed)*.

## A. High-level architecture

```mermaid
flowchart LR
  subgraph Untrusted
    C["Client / AI agent"]
    M["Merchant cart + signed closed mandate"]
  end
  subgraph VILR["VILR gateway (FastAPI process)"]
    API["routes.py: /v1/authorize, /v1/execute"]
    GW["GatewayOrchestrator"]
    VER["VILRMandateVerifier (PyJWT ES256) + JCS cart hash"]
    SEM["AISemanticVerifier"]
    POL["OPAPolicyEngine (HTTP client)"]
    IDM["RedisIdempotencyStore"]
    EXE["PaymentExecutor"]
    LED["Audit ledger (Memory or Supabase)"]
  end
  C --> API
  M --> C
  API --> GW
  GW --> VER
  GW --> IDM
  GW --> SEM
  GW --> POL
  GW --> EXE
  GW --> LED
  SEM -->|"google-genai"| GEM["Gemini API"]
  POL -->|"HTTP /v1/data/vilr/authorization/decision"| OPA["OPA server + authorization.rego"]
  IDM --> RED[("Redis")]
  EXE --> PROV["MockRazorpayProvider (default) or RazorpayPaymentProvider (CLI only)"]
  LED --> SB[("Supabase audit_ledger table")]
```
**Reading it:** the dashed trust boundary is the left box — everything the client sends is hostile, *including the public keys*. Gemini, OPA, Redis, the provider and Supabase are separate network dependencies; each is a failure point (Diagram G). OPA is a **networked** service here (HTTP), not in-process.

## B. End-to-end sequence (authorize then execute)

```mermaid
sequenceDiagram
  autonumber
  participant Cl as Client
  participant API as FastAPI
  participant GW as Gateway
  participant V as Verifier
  participant R as Redis
  participant G as Gemini
  participant O as OPA
  participant A as Audit
  participant P as Provider
  Cl->>API: POST /v1/authorize
  API->>API: Pydantic validation (422 on failure)
  API->>GW: authorize()
  GW->>A: log INTENT_RECEIVED
  GW->>V: verify open JWT (user key from request)
  GW->>A: log AP2_VERIFIED
  GW->>V: verify closed JWT (merchant key from request)
  GW->>GW: recompute cart hash and compare
  GW->>A: log CART_VERIFIED
  GW->>R: SET key NX EX 300 (replay reservation)
  GW->>A: log RESERVATION_ACQUIRED
  GW->>G: semantic assessment (advisory)
  GW->>A: log SEMANTIC_ANALYZED
  GW->>O: POST decision (mandate, cart, semantic, time)
  GW->>A: log POLICY_EVALUATED
  GW->>A: log AUTHORIZED (with evidence)
  GW->>R: SET exec_token NX EX 3600
  GW->>A: log RESERVATION_COMMITTED
  GW-->>Cl: 200 execution_token
  Cl->>API: POST /v1/execute
  API->>GW: execute()
  GW->>R: Lua consume token (4 param checks)
  GW->>GW: PaymentExecutor state guard
  GW->>P: execute_payment (provider idempotency key)
  P-->>GW: SUCCESS / FAILED / UNKNOWN
  GW->>A: log final state
  GW-->>Cl: 200 receipt
```
**Notes:** (1) Audit writes happen *throughout*, not just at the end. (2) The semantic call (slow, paid) happens **after** the cheap deterministic checks (crypto, cart hash, Redis) and **before** OPA — good cost ordering; OPA could have run first but needs the semantic status as an input. (3) No provider call is reachable before `consume_execution_token` succeeds.

## C. Authorization decision flow

```mermaid
flowchart TD
  S["POST /v1/authorize"] --> V0{"Pydantic schema valid?"}
  V0 -- no --> R422["HTTP 422"]
  V0 -- yes --> V1{"Open JWT: ES256 sig, exp, iat OK?"}
  V1 -- "expired" --> E1["MANDATE_EXPIRED 400"]
  V1 -- "bad sig" --> E2["INVALID_SIGNATURE 401"]
  V1 -- ok --> V2{"Closed JWT valid?"}
  V2 -- "bad (state bug, see Ch.4)" --> E3["raises InvalidStateTransition 409 - still denied"]
  V2 -- ok --> V3{"hash(cart) == closed.cart_hash?"}
  V3 -- no --> E4["HASH_MISMATCH 400"]
  V3 -- yes --> V4{"Redis SET NX reservation"}
  V4 -- "key exists" --> E5["REPLAY_DETECTED 409"]
  V4 -- "Redis error" --> E6["IdempotencyUnavailable - 400 via VILRError handler"]
  V4 -- acquired --> V5["Gemini assessment"]
  V5 -- "any error" --> V5F["assessment = FAIL (fail-closed)"]
  V5 --> V6{"OPA allow?"}
  V5F --> V6
  V6 -- "OPA unreachable" --> E7["PolicyUnavailable - release reservation - 400"]
  V6 -- "deny: budget, currency, merchant, semantic FAIL/REVIEW" --> E8["POLICY_DENIED 403 - release reservation"]
  V6 -- allow --> OK["issue execution_token (HTTP 200)"]
```
**Important:** `MerchantUntrusted` is declared and has a handler but is **never raised** anywhere in `app/` (VERIFIED by grep) — there is no merchant trust list at the gateway except the Rego `allowed/prohibited_merchants` lists.

## D. Cryptographic verification — what is actually signed/hashed

```mermaid
flowchart TD
  subgraph User["Open mandate (user key, ES256 JWT)"]
    OC["claims: iss, sub, iat, exp, mandate_id, intent_hash, constraints"]
  end
  subgraph Merchant["Closed mandate (merchant key, ES256 JWT)"]
    CC["claims: iss, iat, exp, mandate_id, open_mandate_hash, cart_hash"]
  end
  CART["Cart from request body"] --> CJ["compute_checkout_hash: JCS(merchant_id, currency, total_amount, items[item_id, quantity, unit_price, currency]) then SHA-256 then base64url"]
  CJ --> CMP{"== cart_hash claim?"}
  CC --> CMP
  OC -. "NOT recomputed or compared (missing)" .-> CC
  INT["request.user_intent.raw_prompt etc."] -. "NOT compared with intent_hash (missing)" .-> OC
  OC --> OPAIN["constraints become OPA input.mandate"]
```
**What is signed:** the two JWTs (signature over `header.payload` with ECDSA P-256 + SHA-256). **What is hashed:** only the **cart** (RFC 8785 JCS bytes → SHA-256 → base64url). **Dotted edges are the missing bindings** (verified by P2/P7). Cart hash covers `merchant_id, currency, total_amount` and item `item_id, quantity, unit_price, currency` — it does **not** cover item `name`, `category`, `brand`. So a merchant-side swap of the *name* shown to Gemini after signing would not break the hash.

## E. Concurrency and replay protection (real Redis operations)

```mermaid
flowchart TD
  subgraph RES["Replay reservation key = open_mandate_hash:cart_hash"]
    N["no key"] -->|"SET NX EX 300 returns OK (try_reserve)"| R["reserved"]
    R -->|"second SET NX returns nil, so ReplayDetected"| R
    R -->|"release Lua DEL, owner only (semantic or policy failure)"| N
    R -->|"TTL 300 s passes, commit never called"| X["expired, same as no key (gap)"]
    X -->|"same mandate+cart can be reserved again"| R
  end
  subgraph TOK["Execution token key = vilr:exec_token:token"]
    A["available"] -->|"Lua consume: tx_id, amount, currency, merchant, mandate_hash all equal"| C["consumed"]
    A -->|"parameter mismatch: PARAM_MISMATCH, token NOT consumed"| A
    C -->|"any later consume: ALREADY_CONSUMED, DuplicateExecution 409"| C
  end
  AUTH["after AUTHORIZED: SET NX EX 3600"] --> A
```
Two key spaces: the **replay reservation** (key = `"<open_mandate_hash>:<cart_hash>"`, no prefix — `build_idempotency_key()` with the `vilr:idempotency:` prefix exists but is **unused**) and the **execution token** (`vilr:exec_token:<token>`). The `commit` Lua script and its `committed` status/24 h TTL exist but the gateway never calls them (VERIFIED by grep).

## F. Audit chain

```mermaid
flowchart LR
  G0["GENESIS = 64 zeros"] --> R1
  subgraph R1["record 1 (INTENT_RECEIVED)"]
    d1["fields + nonce + timestamp + prev_record_hash = GENESIS"] --> h1["record_hash = SHA256(canonical JSON of all fields except record_hash)"]
  end
  R1 --> R2
  subgraph R2["record 2 (AP2_VERIFIED)"]
    d2["fields + prev_record_hash = record1.record_hash"] --> h2["record_hash"]
  end
  R2 --> RN["... one record per state change, per transaction_id"]
  RN --> VER["verify_chain(tx): replay from GENESIS, check prev link and recomputed hash for each row"]
```
Constructed in `GatewayOrchestrator._log` (reads latest record → uses its `record_hash` as `prev_record_hash`) and `build_record`; stored via `MemoryAuditLedger.record` (list) or `SupabaseAuditLedger.record` (`insert` of `{transaction_id, record JSON}`); verified by `verify_chain` (exposed at `GET /v1/audit/{tx}/verify`). **Per-transaction chains only; no global chain, no signature, no external anchor.**

## G. Failure and recovery

```mermaid
flowchart TD
  F1["Invalid input"] --> A1["422 or typed 4xx - no side effects"]
  F2["Gemini error/timeout/bad JSON"] --> A2["AISemanticVerifier returns FAIL, so OPA denies SEMANTIC_FAIL, reservation released"]
  F3["OPA down/timeout/5xx"] --> A3["PolicyUnavailable, reservation released, deny"]
  F4["Redis down at authorize"] --> A4["IdempotencyUnavailable, deny"]
  F5["Redis down at execute"] --> A5["raw RedisError, HTTP 500, no payment (fail-closed)"]
  F6["Provider timeout (real client path)"] --> A6["UNKNOWN, PAYMENT_UNKNOWN, token already consumed so no auto-retry"]
  A6 --> A6b["resolve_unknown() exists on the gateway but has NO HTTP route (missing)"]
  F7["Process crash after token consumed"] --> A7["in-memory state lost: /execute can never proceed - money not moved, token burned (no recovery path, missing)"]
  F8["Provider success then crash before audit"] --> A8["payment exists, audit missing, no outbox or reconciliation job (missing)"]
  F9["Supabase insert fails"] --> A9["exception logged and swallowed, flow continues (audit fail-open)"]
```
**Consequences:** the system fails *closed* for authorization (every authorization dependency failure denies) and *open* for audit. The recovery story for ambiguous payment outcomes is partly designed (`PAYMENT_UNKNOWN`, `reconcile`) but not wired end-to-end.

---

# Chapter 4 — The "seven-stage pipeline", audited

## 4.1 What the repo actually says
- The CV phrase "**seven-stage pipeline** involving Gemini, cryptography, OPA, Redis, Razorpay, Supabase" has **no named counterpart** in the code. `grep -ri "seven\|7-stage"` finds nothing. (VERIFIED.)
- README "ARCHITECTURE": `Gemini → Crypto → OPA → Redis → PaymentExecutor → Razorpay → Supabase` — **seven components**, DOCUMENTED, but **not the real order**.
- README: "Three deterministic authorization layers" ≈ "(Crypto, Redis, OPA)". DOCUMENTED; code consistent.

## 4.2 The real order (VERIFIED, `gateway.py`)
**Crypto → (cart-hash) → Redis → Gemini → OPA → token → [second call] Redis token consume → PaymentExecutor → Razorpay**, with Supabase audit on every state change. Gemini is *after* Crypto and Redis, *before* OPA — not first.

## 4.3 A faithful 7-stage grouping (my derivation — INFERRED, not a name used in the repo)

| # | Stage | Function / location | Receives | Produces | Checks | State read/written | Trusts | Rejects with | Next |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Intake & validation** | FastAPI + `AuthorizeRequest`; `authorize()` start (`gateway.py:138-152`) | JSON body | typed request; `INTENT_RECEIVED`; audit #1 | types, `Decimal`, currency regex `^[A-Z]{3}$`, `quantity ≥ 1`, `Money ≥ 0`, non-empty ids | **resets** `_tx_states[tx_id]` (line 143) | nothing | 422 | 2 |
| 2 | **Mandate cryptography** | `verify_open/closed_checkout_mandate` (lines 156-165) | two JWTs, two JWKs (from request) | `OpenCheckoutMandate`, `ClosedCheckoutMandate`; `AP2_VERIFIED` | ES256 only; `exp`,`iat` required; 30 s leeway; JWK must be EC P-256 | state, audit | the **supplied** keys | `InvalidSignature` 401 / `MandateExpired` 400 / `InvalidRequest` 400 | 3 |
| 3 | **Cart binding** | `compute_checkout_hash` compare (170-172) | `request.cart`, `closed.cart_hash` | `CART_VERIFIED` | JCS+SHA-256 equality | state, audit | cart_hash claim | `HashMismatch` 400 | 4 |
| 4 | **Replay reservation (Redis)** | `idempotency.try_reserve` (205-207) | `"<open_mandate_hash>:<cart_hash>"`, tx_id | `RESERVATION_ACQUIRED` | atomic `SET NX EX 300` | **writes Redis** | the `open_mandate_hash` claim (unverified) | `ReplayDetected` 409; Redis error → `IdempotencyUnavailable` | 5 |
| 5 | **Semantic assessment (Gemini)** | `semantic.verify` (233-247) | intent + cart | `SemanticAssessment`; `SEMANTIC_ANALYZED` | schema-validated model output; **never raises** (errors → `FAIL`) | audit | nothing (advisory) | on unexpected exception: release reservation, re-raise | 6 |
| 6 | **Policy decision + token issuance (OPA)** | `policy.evaluate`, evidence build, token creation (250-374) | signed constraints, cart, semantic status, now | `AuthorizationDecision`; `AUTHORIZED`; `execution_token`; `RESERVATION_COMMITTED` | Rego rules (Ch. 7) | Redis token `available`, audit | OPA | `PolicyDenied` 403 (release reservation); `PolicyUnavailable` | 7 |
| 7 | **Execution** | `execute()` → `consume_execution_token` → `PaymentExecutor.execute` → provider (381-458) | token + amount/currency/merchant/mandate_hash/idem key | `ExecutionReceipt`; `PAYMENT_*` | Lua: ownership, unconsumed, 4 equalities; state guard | Redis token → `consumed`; in-memory state; audit | token (bearer) | 409 duplicate; 400 mismatch; 409 state | end |

Where this fits the CV: Gemini (5), cryptography (2–3), OPA (6), Redis (4, 7), Razorpay (7), Supabase (audit in all). **Safe interview phrasing:** *"The gateway has a staged flow — I usually describe it as seven checkpoints: validation, mandate crypto, cart binding, replay reservation, semantic evidence, OPA policy, and token-gated execution — with the audit chain written at every transition."* Say "I group it as…", not "the code defines seven stages".

## 4.4 Ordering and security dependencies (checked, not assumed)
- **Cheap before expensive:** signature/hash/Redis (µs–ms) run before Gemini (≈1–2.5 s documented) and OPA. ✔ (VERIFIED order.) Consequence: a flood of valid-looking-but-replayed requests is stopped at Redis before costing a model call. A flood of *new* valid mandates still costs model calls (no rate limiting — grep finds none).
- **Side effects before authorization finishes?** Yes, two benign ones: audit writes (from stage 1) and the Redis reservation (stage 4, *before* Gemini/OPA). The reservation is released on semantic exception / policy denial / OPA outage (`release` Lua; owner-only). Stages 2–3 run *before* the reservation, so they have nothing to release. The *payment* side effect cannot occur until stage 7. ✔
- **Provider before all authorization done?** No. `execute()` cannot reach the provider without a token that exists only after `AUTHORIZED`. ✔ (test: `test_unauthorized_cannot_invoke_executor`, `test_pa_11`.)
- **Dependency:** stage 6 consumes stage 5's output; stage 7 consumes stage 6's token; the signed `constraints` (stage 2) — not the request's `user_intent.hard_constraints` — feed OPA. ✔ (`open_mandate.constraints.model_dump` at line 252.)

## 4.5 Two complete paths

**Legitimate (V-01 + V-02 in the simulator):** stages 1→7 as above; audit has ≈ 9 records (`INTENT_RECEIVED, AP2_VERIFIED, CART_VERIFIED, RESERVATION_ACQUIRED, SEMANTIC_ANALYZED, POLICY_EVALUATED, AUTHORIZED, RESERVATION_COMMITTED`, then a final record at the execution state); provider `payment_creation_count == 1`. (My run: V-01 and V-02 PASS.)

**Malicious — cart tampering (T-03, PASS in my run):** attacker changes `cart.total_amount` to `"1.00"` after the merchant signed → stage 3 recomputes hash ≠ `cart_hash` → `HashMismatch` → state `HASH_MISMATCH` + risk `CART_MISMATCH` (weight 80) → audit record → HTTP 400. Redis and Gemini are never touched; provider never reached.

**Malicious — replay (T-04/T-22, PASS):** second identical request → stage 4 `SET NX` returns nil → `REPLAY_DETECTED` → HTTP 409. (T-22 passes because the Redis key ignores `transaction_id`; changing it doesn't help the attacker *within 300 s*.)

## 4.6 A real bug in the failure path (VERIFIED by my run: T-07/T-11/T-14 return **409**, not 401)
`VALID_TRANSITIONS[AP2_VERIFIED]` allows only `CART_VERIFIED`, `HASH_MISMATCH`, `MERCHANT_UNTRUSTED`. If the **closed** mandate fails (`InvalidSignature` / `MandateExpired`) the handler does `state.transition_to(INVALID_SIGNATURE)` which itself raises `InvalidStateTransition`. Result: the request is still denied (fail-closed ✔) but with the wrong HTTP code (409 instead of 401/400), and the failure audit record and risk evidence for closed-mandate failures are **not written**. Good example of "denied for the right outcome, wrong reason" — keep it in your back pocket.

---

*Continue with [02_ai_crypto_policy.md](02_ai_crypto_policy.md).*
