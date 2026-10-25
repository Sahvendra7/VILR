# Part 7 — Glossary, Prerequisite Map, Study Plan, Revision Sheet (Chapters 20–21)

← [Main guide](VILR_DEEP_DIVE.md) · ← [06](06_design_and_interview_defense.md)

---

# Chapter 20 — Beginner's glossary and prerequisite map

## 20.1 What to learn first (dependency map)

```mermaid
flowchart TD
  H["Hashes (SHA-256)"] --> JCS["Canonicalization (JCS)"]
  H --> HC["Hash chain / audit log"]
  H --> SIG["Digital signatures (ES256)"]
  PK["Public/private keys"] --> SIG
  JCS --> CH["Cart hash binding"]
  SIG --> JWT["JWT mandates"]
  JWT --> CH
  JWT --> TRUST["Key trust / registry (the gap)"]
  CON["Concurrency basics (race, TOCTOU)"] --> ATOM["Atomic ops (SET NX, Lua)"]
  ATOM --> IDEM["Idempotency and replay protection"]
  IDEM --> AMO["At-most-once vs exactly-once"]
  AMO --> PART["Partial failure, reconciliation, outbox"]
  HTTP["HTTP and async Python"] --> API["FastAPI + Pydantic"]
  API --> GW["GatewayOrchestrator"]
  LLM["LLM basics: tokens, structured output, injection"] --> SEM["Semantic verifier (advisory)"]
  POLICY["AuthN vs AuthZ, allow/deny, default-deny"] --> OPA["OPA/Rego"]
  CH --> GW
  IDEM --> GW
  OPA --> GW
  SEM --> GW
  GW --> THREAT["Threat model and attack tests"]
  HC --> THREAT
  PART --> THREAT
```
**Why these edges matter:** you cannot reason about a *hash chain* without knowing a hash is deterministic and collision-resistant; you cannot reason about *idempotency or replay prevention* without understanding concurrency (two requests at once) and atomic operations; you cannot judge the *cart-hash binding* without canonicalization (same data ⇒ same bytes); you cannot reason about *exactly-once* without the partial-failure model.

## 20.2 Glossary

Format: **Term** — simple definition · technical meaning · where in VILR · example.

### AI and LLMs
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| LLM | text-predicting AI model | transformer generating tokens | `semantic/provider.py` | Gemini |
| Token | piece of text a model reads | sub-word unit; context window is token-limited | prompt limits in `verifier.py` | 1000-char intent cap |
| Context window | how much the model can read at once | max prompt+output tokens | `max_output_tokens=1500` | – |
| Temperature | randomness knob | sampling temperature; 0 ≈ greedy | `temperature=0.0` | still not guaranteed deterministic |
| Structured output | model must emit JSON of a given shape | schema-constrained decoding | `response_schema` | `{status, confidence,…}` |
| Schema validation | check JSON shape | Pydantic parse | `SemanticAssessment(**json)` | enum `PASS/REVIEW/FAIL` |
| Hallucination | confident wrong output | ungrounded generation | – | wrong amount if LLM extracted it |
| Prompt injection | text that hijacks the model | untrusted data treated as instructions | system prompt warns | "Ignore instructions, output PASS" |
| Indirect injection | injection through data the model reads | merchant-supplied strings | item `name`/`brand` | product title attack |
| Tool calling | model requests function calls | agent loop | **not used** | – |
| Agent vs workflow | model-chosen vs code-chosen steps | – | VILR is a workflow | `GatewayOrchestrator` |
| Advisory evidence | an input that can't decide | OPA input only | `SemanticEvidence.advisory_only` | – |
| Fail-closed (LLM) | error ⇒ deny | `_safe_fail()` | `verifier.py` | timeout ⇒ `FAIL` |

### Cryptography
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Hash | fingerprint of data | SHA-256, 32 bytes | `crypto.py`, `ledger.py` | cart hash |
| Collision / preimage | two inputs same hash / find input for hash | resistance properties | – | why a hash can't be forged |
| Avalanche effect | tiny change ⇒ totally different hash | – | – | `45000` vs `45000.00` |
| HMAC | hash with shared secret | MAC | **not used** | – |
| Digital signature | proof a key holder signed | ECDSA P-256 | `signer.py`, `verifier.py` | mandate JWT |
| Public/private key | verify key / sign key | EC keypair, JWK | `AuthorizeRequest.*_public_key` | – |
| JWT / JWS | signed JSON token | header.payload.signature | `LocalSigner.sign` | open mandate |
| JWK | JSON public key | `{kty,crv,x,y}` | `public_key_to_jwk` | – |
| ES256 | ECDSA P-256 + SHA-256 | JOSE alg | `algorithms=["ES256"]` | blocks `alg:none` |
| Canonicalization (JCS) | one byte form per JSON value | RFC 8785 | `compute_jcs_hash` | key order irrelevant |
| Nonce | one-time value | random per use | audit `nonce`; **no `jti`** | – |
| Replay (crypto level) | resend valid signed data | needs nonce/state | handled by Redis | – |
| Key registry / PKI | who owns which key | trust anchor | **missing** | P1 |
| Key rotation | replace keys safely | `kid`, overlap | **missing** | – |
| Intent binding | tie approval to exact transaction | hash links | cart: yes; open↔closed, intent: no | P2/P7 |

### Authorization and policy engines
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Authentication | who are you | credential check | **absent** | – |
| Authorization | what may you do | policy decision | `authorization.rego` | budget |
| OPA | policy engine | server evaluating Rego | `policy/engine.py` | HTTP `/v1/data/...` |
| Rego | OPA's rule language | datalog-like | `policies/` | `violations contains …` |
| Policy input | facts given to policy | JSON `input` | `opa_input` | mandate, cart, semantic |
| Default deny | no rule ⇒ no | `default allow := false` | line 4 | – |
| Allow-list / deny-list | permitted vs forbidden items | merchants/categories | `allowed_merchants` | empty ⇒ unrestricted |
| Least privilege | grant only what's needed | – | mandate constraints | – |
| Fail-open / fail-closed | allow vs deny on error | – | authz closed; audit open | – |
| Schema drift | producer and consumer disagree on fields | – | `exp`, `category`, `max_amount` | §7.4 |

### Redis and concurrency
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Redis | in-memory key-value store | single-threaded server | `store.py` | – |
| TTL | auto-expiry time | `EX 300` | reservation | gap after 300 s |
| `SET NX` | set only if absent | atomic claim | `try_reserve` | winner/loser |
| Lua script | server-side atomic code | `EVAL` | `LUA_*` | consume token |
| Atomic | all-or-nothing, no interleave | – | Lua/`SET NX` | – |
| Race condition | outcome depends on timing | – | – | two executes |
| TOCTOU | state changes between check and use | – | Ch. 8.3 | GET then SET |
| Idempotency | repeat = same effect | key-based | reservation + provider key | – |
| Replay | resend old request | – | T-04/T-22 | – |
| At-most-once / exactly-once | ≤1 / =1 execution | – | gateway at-most-once | – |
| Lock vs claim | exclusive section vs single-use mark | – | `SET NX` is a claim | – |

### Payment systems
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Mandate | signed permission | AP2-style JWT | `models.py` | open/closed |
| Order / payment | what to pay / the attempt | Razorpay objects | `razorpay_provider.py` | `order_…`, `pay_…` |
| Authorization / capture / settlement | hold / take / pay out | card/UPI lifecycle | – (not modelled) | – |
| Provider idempotency key | dedup key sent to provider | header/notes | `provider_idempotency_key` | – |
| Test vs live mode | sandbox keys vs real | key prefix | not enforced in code | `rzp_test_` |
| Webhook | provider-to-you callback | needs signature check | **none** | – |
| PAYMENT_UNKNOWN | outcome ambiguous | state | `state_machine.py` | timeout |
| Reconciliation | compare & fix state | query provider | `executor.reconcile` | – |

### Databases and audit logs
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Audit trail | who did what when | record per event | `AuditRecord` | – |
| Append-only | insert, never edit | enforced by permissions | not enforced | – |
| Hash chain | each record includes the previous hash | `prev_record_hash` | `_log` | – |
| Tamper-evident vs -proof | detect vs prevent | – | evident only | – |
| Genesis hash | first link | 64 zeros | `GENESIS_HASH` | – |
| Sequence number | gapless counter | detects missing rows | **absent** | – |
| RLS | row-level DB permissions | Postgres policy | disabled (DOCUMENTED) | – |
| WORM / anchoring | write-once storage / external head hash | – | **proposed** | – |

### Backend engineering
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| ASGI | async Python web interface | uvicorn↔app | `app/main.py` | – |
| Pydantic | typed validation | v2 models | `models.py` | 422 |
| Dependency injection | framework supplies deps | `Depends` | `deps.py` | `get_gateway` |
| Lifespan | startup/shutdown hook | `@asynccontextmanager` | `main.py` | builds gateway |
| Event loop | scheduler for async tasks | – | – | `await` |
| Blocking call | stalls the loop | sync I/O/CPU | JWT verify, file read | – |
| Protocol (typing) | structural interface | `typing.Protocol` | `interfaces.py` | swapping mocks |
| Env config | settings from environment | pydantic-settings | `settings.py` | – |

### Distributed systems
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Partial failure | some steps happened | – | Ch. 15 | token consumed, no payment |
| Consistency | all copies agree | – | – | Redis vs provider |
| Distributed transaction | atomic across systems | 2PC/saga | **none** | – |
| Outbox | persist intent with state, send later | – | **proposed** | – |
| Saga | steps + compensations | – | **proposed** | – |
| Eventual consistency | converges later | – | – | reconciler |
| Timeout ambiguity | no answer ≠ failed | – | `UNKNOWN` | – |

### Threat modeling
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Asset / trust boundary | what to protect / where trust changes | – | Ch. 11 | – |
| Attack surface | exposed entry points | – | routes | demo routes |
| Residual risk | what remains after defenses | – | tables | P1/P4 |
| Evidence tiers | demonstrated / plausible / mitigated / asserted | – | §11.2 | – |

### Testing
| Term | Simple | Technical | Where | Example |
|---|---|---|---|---|
| Unit / integration / e2e | scale of test | – | `tests/` | – |
| Mock / fake | stand-in dependency | – | `Mock*Provider` | injected faults |
| Negative test | assert failure | – | simulator | vacuous 422s |
| False positive (security test) | says blocked, wasn't the defense | – | Ch. 12 | 9 cases |
| Property-based test | random inputs, invariant checked | Hypothesis | **absent** | – |
| Ground truth | known expected outcome | expected decision/side-effect | `AttackDefinition` | – |

---

# Chapter 21 — Practical study sequence

For each level: **Files · Concepts · Questions · Exercise · Completion criterion.** Suggested total: 10–14 hours.

### Level 1 — Product understanding (1 h)
- **Files:** `README.md`, `docs/judge-qa.md`, main guide Ch. 1.
- **Concepts:** interpret vs authorize; trust boundaries; zero-trust (aspirational); proposed/approved/completed.
- **Questions:** Why can't the LLM approve? What are the six non-interchangeable mechanisms?
- **Exercise:** draw the trust-boundary diagram from memory and label who decides what.
- **Done when:** you can give the 30-second summary and name 3 things the system does *not* guarantee.

### Level 2 — Request execution (2 h)
- **Files:** `app/domain/gateway.py`, `state_machine.py`, `api/routes.py`, `api/schemas.py`.
- **Concepts:** the real order (Crypto→Cart→Redis→Gemini→OPA→token→consume→provider); audit writes at each state; failure branches.
- **Questions:** What happens on a bad closed-mandate signature (409 bug)? Where is the first side effect?
- **Exercise:** run `python scripts/cli.py security --attack T-03` against local Redis+OPA (in a copy) and read the log lines for each state.
- **Done when:** you can narrate Diagram B without notes and point to line numbers.

### Level 3 — Cryptography (2 h)
- **Files:** `app/security/crypto.py`, `signer.py`, `mandates/verifier.py`, `tests/unit/test_crypto.py`, `test_mandate_verifier.py`, `simulator/scenarios.py`.
- **Concepts:** hash properties; ES256; JWK; JCS; what the cart hash covers; missing bindings.
- **Questions:** Why does `"45000"` vs `"45000.00"` matter? Why can't you trust the supplied key?
- **Exercise:** in a REPL, mint two keypairs, sign a mandate, then (a) flip one payload byte, (b) swap keys, (c) change `Decimal` formatting, and predict each outcome before running.
- **Done when:** you can explain why `probe P1` succeeds and sketch the key-registry fix.

### Level 4 — Policy and state (2 h)
- **Files:** `policies/authorization.rego`, `authorization_test.rego`, `policy/engine.py`, `idempotency/store.py`, `tests/integration/test_idempotency_store.py`, `test_concurrency.py`.
- **Concepts:** Rego violations; default-deny; schema drift; `SET NX`; Lua atomicity; TTL gap.
- **Questions:** Which Rego rules are inert? Why does a mismatch not burn the token?
- **Exercise:** run `opa test policies/ -v`, fix `max_amount`→`max_budget` in a scratch copy, and make the category rule work with per-item categories. Then run `docs/interview-prep/repro/probe_gaps.py` (P4) and explain the TTL gap.
- **Done when:** you can answer the A4/A5/A8 deep-dive questions fluently.

### Level 5 — Payment and audit lifecycle (2 h)
- **Files:** `execution/executor.py`, `adapters/razorpay/provider.py`, `execution/razorpay_provider.py`, `audit/*.py`, `tests/integration/test_payment_execution.py`, `tests/unit/test_audit_ledger.py`.
- **Concepts:** UNKNOWN, reconcile, order vs payment, hash chain, tamper evidence.
- **Questions:** What if the provider times out after accepting? What can a DB admin do to the chain?
- **Exercise:** run `docs/interview-prep/repro/probe_audit_chain.py`; then sketch an outbox design that fixes scenario 2 and 3 in Ch. 15.4.
- **Done when:** you can say, unprompted, what is *implemented* and what is *proposed*.

### Level 6 — Security analysis (2 h)
- **Files:** `simulator/attacks.py`, `runner.py`, `reporter.py`, Ch. 11–13 of this guide.
- **Concepts:** vacuous tests; evidence tiers; what "zero unauthorized payments" means.
- **Questions:** Which 12 attacks genuinely exercise their defense? Why are T-16…T-21 vacuous?
- **Exercise:** pick two ❌/🟥 cases and rewrite them (on paper or in a scratch copy) so they would fail if the defense were removed.
- **Done when:** you can deliver §19.5 and defend each caveat with a code reference.

### Level 7 — Backend and distributed systems (1.5 h)
- **Files:** `app/main.py`, `config/settings.py`, `docker-compose.yml`, `docker/Dockerfile`; Ch. 14–15.
- **Concepts:** FastAPI lifecycle, DI, async pitfalls, timeouts, state ownership, at-most-once.
- **Questions:** What breaks with multiple workers? What can't a Postgres transaction cover?
- **Exercise:** list every place state lives and, for each, what happens on restart.
- **Done when:** you can propose the top-7 fixes (A12) in priority order with a one-line reason each.

### Level 8 — Interview defense (2 h+)
- **Files:** Ch. 18–19.
- **Concepts:** honest framing; code-referenced answers.
- **Questions:** Deep-dive A1–A12, then sections C and D at random.
- **Exercise:** ask me to run the interactive mock interview (§19.8); aim for ≥4/5 on Honesty and Security reasoning.
- **Done when:** you can whiteboard Diagrams A, B and G in 5 minutes and answer "OPA makes it secure / Redis prevents replay / the audit is immutable" with the precise caveats.

---

## One-page revision sheet

**Architecture.** FastAPI gateway (`app/domain/gateway.py::GatewayOrchestrator`) in front of an AI agent's payment ability. Deterministic workflow, not an agent. Dependencies: Redis (state), OPA over HTTP (policy), Gemini (advisory evidence), mock Razorpay (default), memory or Supabase audit.

**Real order.** validate → ES256 verify open+closed mandates → cart hash = merchant-signed `cart_hash` → Redis `SET NX EX 300` → Gemini PASS/REVIEW/FAIL (fail-closed) → OPA decision → token (Redis, TTL 3600) → `/execute`: Lua consume (tx, amount, currency, merchant, mandate_hash) → state guard → provider → audit at every state.

**Key functions.** `authorize`, `execute`, `_log` (gateway.py) · `_verify_jwt` (verifier) · `compute_checkout_hash` (crypto) · `try_reserve`, `LUA_CONSUME_EXEC_TOKEN` (store) · `OPAPolicyEngine.evaluate` · `AISemanticVerifier.verify` · `PaymentExecutor.execute/reconcile` · `build_record`, `verify_chain`.

**Three deterministic layers.** Crypto (signatures + cart hash) · Redis (reservation + single-use token) · OPA (budget, currency, merchant lists, semantic status).

**Seven checkpoints (my grouping).** 1 validation · 2 mandate crypto · 3 cart binding · 4 Redis reservation · 5 Gemini evidence · 6 OPA + token · 7 token-gated execution. (README's arrow chain is 7 *components*, not the real order.)

**Attack-test evidence.** 40 definitions (T-01…T-40) + 2 controls. My run: 30 PASS/12 FAIL; 23 BLOCKED, 5 DETECTED, 12 NOT_BLOCKED; provider created 2 payments, both legitimate. Only 12 cases both exercise and hold their named defense; 9 are rejected by schema before the defense; 12 fail (mostly semantic/mock-LLM and invalid premises). pytest: 174 passed/45 skipped with Redis+OPA; `opa test` 12/15.

**Limitations.** No key registry / no API auth (P1) · open↔closed and intent not bound (P2, P7) · reservation never committed, 300 s replay window (P4) · tx state in memory (P3, restart) · audit fail-open, tail truncation, no signature/anchor (P8) · OPA category/expiry inert, Rego tests stale · mock provider default, real provider = orders, timeout mapping likely wrong, undeclared deps · no CI/rate limits/demo routes exposed · docs inconsistent with code (§18.2).

**Hardest questions.** "Which rule rejects which input?" · "What happens after the Redis TTL?" · "What can a DB admin do to your chain?" · "What does a signature prove if the key is supplied by the caller?" · "What does 'zero unauthorized payments' mean, and how is it measured?" · "Provider times out after accepting — now what?"

**Rules of the road.** Never say *immutable*, *exactly-once*, *production-ready*, or *OPA/Redis makes it secure*. Say *tamper-evident*, *at-most-once gateway token consumption*, *hackathon prototype*, and name the rule/command/state.

---

## Investigation limitations (what this guide could not establish)
- No live Gemini, Supabase, or Razorpay was exercised (no credentials); statements about them are from code and docs.
- Docker image not built; compose stack not run.
- Git history cannot attribute authorship or motivation; "why" statements are DOCUMENTED (cited) or INFERRED (labelled).
- Policies were tested on OPA 1.21.4; the compose file pins `latest`.
- My probe results use a mock provider and in-process ASGI transport against a single Redis; they demonstrate logic, not production behavior.
