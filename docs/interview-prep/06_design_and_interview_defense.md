# Part 6 — Design Decisions and Interview Defense (Chapters 18–19)

← [Main guide](VILR_DEEP_DIVE.md) · ← [05](05_backend_distsys_algos_stack.md) · Next → [07_glossary_and_study_plan.md](07_glossary_and_study_plan.md)

> **Rule for every answer below:** describe what the code does (VERIFIED), why the design is reasonable (INFERRED unless a doc states it), and what it doesn't guarantee. Never claim that you personally made a decision or debugged something unless you actually did — the git history cannot back that up (all 20 commits are by "Antigravity Agent").

---

# Chapter 18 — Design decisions and alternatives

## 18.1 Decision table

| Decision | Current implementation | Why it could be reasonable | Alternative | Trade-offs | Evidence / motivation source |
|---|---|---|---|---|---|
| **Separate LLM interpretation from authorization** | Gemini → `SemanticAssessment`; OPA/crypto/Redis decide | LLMs are non-deterministic and injectable; rules are testable and explainable | Let an agent with tools call a pay function guarded by prompts | Extra layers/latency; semantic cases rely on a probabilistic judge | **DOCUMENTED** motivation: README "AI can interpret and recommend. AI cannot authorize money movement"; `docs/judge-qa.md` Q3–Q5. **VERIFIED** in code + `test_tier2a_*` |
| **Cryptographic mandate binding (AP2-style JWTs)** | ES256 open mandate (user) + closed mandate (merchant); cart hash via JCS+SHA-256 | Prevents post-signing cart tampering; standard JWT tooling | Plain server-side session state; HMAC with shared secret | Needs key distribution (not implemented); complexity | **DOCUMENTED**: `docs/ap2-boundary.md` ("AP2-style … simplified", "Do not claim full AP2 conformance"). Gap: open↔closed link claimed in docs but not verified in code |
| **Policy engine = OPA over HTTP** | `OPAPolicyEngine` POSTs to `/v1/data/vilr/authorization/decision`; Rego with `default allow := false` | Declarative, testable, auditable rules separate from code; hot-reloadable | Python predicates; embedded OPA/WASM; Cedar | Network hop & outage mode; schema drift (§7.4) | **DOCUMENTED**: judge-qa Q5. Post-hoc reasoning otherwise |
| **Redis for replay + one-time tokens** | `SET NX EX`, 3 Lua scripts | Atomic primitives, low latency, simple TTL expiry | Postgres unique constraint / `UPDATE … RETURNING`; Redlock | volatile unless persisted; TTL gap; not atomic with provider | **DOCUMENTED**: judge-qa Q6/Q7, `docs/idempotency.md`, claim-audit downgrade to "at-most-once" |
| **Two-step authorize → execute with a bearer token** | `/authorize` returns `execution_token`; `/execute` consumes it with bound params | Lets approval and execution be separate moments; token is single-use | One-shot "authorize+pay" | Token is a bearer secret; extra round trip; state split across calls | **INFERRED** (no stated rationale) |
| **Payment-provider sequencing & states** | `RESERVATION_COMMITTED → EXECUTION_STARTED → CONFIRMED/FAILED/UNKNOWN`; no auto-retry on UNKNOWN | Avoids double charge on ambiguous outcomes | Retry with same idempotency key; saga + reconciler | UNKNOWN needs a reconciler (not wired) | **DOCUMENTED**: judge-qa Q8, `docs/payment-unknown-validation.md`; **VERIFIED** tests PA-03/04/05 vs mock |
| **Audit as per-transaction hash chain** | `prev_record_hash` + SHA-256 per record, Supabase or memory | Cheap tamper evidence, easy verify | Signed log, Merkle tree + anchoring, immutable store | No protection against DB admin; fail-open writes | **DOCUMENTED**: claim-audit replaced "immutable/WORM" with "tamper-evident"; judge-qa Q17–Q18 |
| **Error handling: typed exceptions → HTTP codes** | `VILRError` hierarchy + handlers | Clear client semantics, centralized mapping | RFC 7807 problem+json | Several outages map to generic 400 | **INFERRED** |
| **Fail-closed on authorization dependencies** | Gemini error → `FAIL`; OPA error → deny; Redis error → deny | Money must not move on uncertainty | Fail-open with monitoring | Availability loss | **DOCUMENTED**: README "securely fails closed on timeouts or schema violations"; **VERIFIED** (Gemini, OPA, Redis authorize) |
| **Fail-open on audit write** | `SupabaseAuditLedger.record` swallows exceptions | Don't block payments on logging | Block/queue (outbox) | Silent audit gaps (P8) | **VERIFIED** (no documented rationale — likely demo robustness; **INFERRED**) |
| **Test-mode integration (mock default, TEST Razorpay optional)** | `MockRazorpayProvider` wired in `main.py`; real provider only via CLI | Safe, deterministic, quota-friendly | Always sandbox | Mock/real divergence (timeout exception types) | **DOCUMENTED**: claim-audit §6, judge-qa Q10/Q16 |
| **Attack-test methodology** | 40 scripted HTTP scenarios + 2 valid controls, ground-truth expected decision & side-effect, mock-provider call counts | Repeatable, comparable across baselines | Fuzzing, property-based, red-team with live model | Many cases are vacuous (Ch. 12) | **VERIFIED** structure; effectiveness weak (my run 30/42 pass) |

## 18.2 Documented claims vs. what the code does (use as a "know your weak spots" cheat sheet)

| Document says | Code says | Source |
|---|---|---|
| "Open and closed mandates are cryptographically linked via `open_mandate_hash`" | linkage never verified (P7a) | `docs/ap2-boundary.md` vs `gateway.py` |
| "Idempotency-Key header is passed to the payment provider" | real provider only puts it in `notes` | `docs/judge-qa.md` Q13 vs `razorpay_provider.py` |
| "Redis … single intent can only generate exactly one execution token" | true only within the 300 s reservation TTL | `judge-qa` Q6 vs P4 |
| "RESERVATION_COMMITTED" returned as `reservation_status: COMMITTED` | store stays `reserved`; `commit()` never called | `routes.py` vs `store.py` |
| "Razorpay TEST … maps to a real `pay_xxx`" | real provider returns an **order** id | claim-audit §6 vs code |
| "Gemini 3.6-flash" / "gemini-3.1-flash-lite" | two different names | README vs claim-audit |
| "40 attack vectors … 0 unauthorized … 16 deterministically blocked" | 23 blocked/12 not blocked in my run; 16 irreproducible | README vs Ch. 12 |
| "Supabase persistent tamper-evident audit" | default is memory; Supabase path not run by me; tail truncation undetected | README vs `main.py` |
| "Quickstart safe demo with real infrastructure" | demo replaces Redis & OPA with fakes | README vs `scripts/cli.py` |
| `docs/limitations.md`: "SQLite audit storage" | no SQLite in code (Supabase/memory) | docs vs code |

---

# Chapter 19 — Interview defense pack

## 19.1 Your individual contribution (evidence-based)
- **What the evidence shows:** a single automated author on all commits (**UNKNOWN** who prompted/guided/reviewed it). The CV states the project; the repo does not document your role.
- **Safe framing (use only what is true for you):** *"I built/led this as a hackathon prototype using AI coding assistance. I can walk through every layer, and I went through the code to audit the claims — here are the gaps I found and what I'd fix first."* If you in fact designed the architecture or wrote parts, say which, and be ready for a code deep-dive on them. If you didn't write parts, that's fine — the strongest signal is understanding and honest limits.
- **Do not claim:** specific bugs you "debugged", performance numbers you didn't measure (`run_metrics.py` prints fake numbers), or "tested against live Razorpay" unless you did.

## 19.2 Spoken summaries

**30 seconds.**
"VILR is a payment gateway that sits between an AI shopping agent and the payment provider. The AI can interpret a request and flag mismatches, but it can't approve money movement. Approval comes from deterministic layers: signed mandates and a cart hash, a Redis single-use reservation and execution token, and an OPA policy for budget and merchant rules. Everything is written to a hash-chained audit log. I tested it with a simulator of forty attack scenarios against a mock payment provider, and I know exactly where the prototype's limits are."

**90 seconds (technical).**
"A request arrives with two ES256-signed mandates — the user's open mandate with spending constraints, the merchant's closed mandate with a hash of the cart — plus the cart itself. The gateway verifies signatures and expiry, re-hashes the cart with RFC 8785 canonical JSON and SHA-256, and takes a Redis `SET NX` reservation keyed by mandate and cart hash. Only then does it ask Gemini for a structured PASS/REVIEW/FAIL assessment of whether the cart matches the user's words; any model failure becomes FAIL. That assessment, plus the signed constraints and the cart, goes to OPA. If OPA allows, the gateway stores a one-time execution token in Redis bound to amount, currency, merchant, and mandate hash. A second call consumes the token with a Lua script — atomically, with all four values compared — and only then touches the provider. Each state change is appended to a hash-chained audit log. The key idea is that the model can only add reasons to deny; it can't create an approval."

**5 minutes (architecture).** Use Diagram B (sequence) and Diagram G (failures) and the 7 checkpoints (Ch. 4.3). Structure: problem (1 min) → trust boundaries (30 s) → the pipeline (2 min) → failure behavior (1 min) → honest limitations (30 s). End with: *"If I had a week: key registry, bind open↔closed mandate and intent hash, commit the reservation with a mandate-nonce, move transaction state to Postgres, and sign/anchor the audit chain."*

**Whiteboard walkthrough.** Draw: `Agent → [VILR: validate → crypto → cart-hash → Redis reserve → Gemini → OPA → token]` then `→ [execute: Lua consume → state guard → provider]` with Supabase on the side. Narrate which box is deterministic. Then draw the three failure arrows: replay (Redis), over-budget (OPA), cart swap (hash). Then volunteer "what this doesn't solve": identity (keys supplied by caller), replay after TTL, atomicity with provider.

## 19.3 "Why LLM output isn't trusted for final authorization"
"Four reasons, each visible in the code. One, it's non-deterministic, so I can't reproduce or unit-test a decision. Two, it reads attacker-controlled text — product names and brands go into the prompt — so it's injectable. Three, it can hallucinate. Four, its output is probabilistic evidence, not a rule I can explain to an auditor. So its output is validated by a Pydantic schema and used only as an input to OPA, where `FAIL` and `REVIEW` add violations. If it says PASS on an over-budget cart, OPA still returns BUDGET_EXCEEDED — I have a test for that. The worst a compromised model can do is cause a false denial." *(Code: `semantic/verifier.py`, `policies/authorization.rego`, `test_security_invariant.py`.)*

## 19.4 The three deterministic layers in one breath
- **Crypto:** ES256 signature + `exp/iat` on both mandates; cart re-hashed via JCS+SHA-256 and compared with the merchant's signed `cart_hash`. *Proves consistency under supplied keys, not identity.*
- **Redis:** `SET NX EX 300` on `(open_mandate_hash:cart_hash)` for replay; a Lua-consumed token binding `(tx, amount, currency, merchant, mandate_hash)` for at-most-once execution.
- **OPA:** default-deny Rego: budget, currency, merchant allow/deny lists, semantic status. *Category and rego-level expiry are inert due to field drift.*

## 19.5 Honest attack-testing methodology
"There are 40 scripted attack definitions plus two valid controls. They run through the real FastAPI app with real Redis and OPA, but with a mock LLM and mock provider. Each case has an expected decision and expected side-effect; side-effects are measured by the mock provider's call counters. When I re-ran it I got 30 pass and 12 fail — the failures are mainly semantic cases that need a live model or whose payloads don't carry the attack — and I found nine execution cases that are rejected by schema validation, so I treat them as covered by the integration tests instead. 'Zero unauthorized payments' held in the suite, but I also found a replay-after-TTL path and request-supplied keys that the suite doesn't cover."

## 19.6 Main limitations (memorize)
1. No trust anchor for keys; no API auth. 2. Open↔closed mandate and intent not bound. 3. Reservation never committed (300 s replay window). 4. Transaction state in process memory; token burn on restart/state clobber. 5. Audit: fail-open, tail-truncation/dropped-write blind spots, no signature/anchor, memory default. 6. OPA: category & expiry inert; Rego tests stale (3/15 fail). 7. Mock provider default; real provider creates *orders*, timeout mapping likely wrong, undeclared deps. 8. Attack suite: 12 failing/vacuous cases; semantic behavior unmeasured with a live model. 9. No CI, no rate limits, demo routes exposed.

---

## 19.7 Question bank

Legend for the **Deep-dive Q&A** block: each has **Spoken answer**, **Reasoning**, **Code**, **Follow-ups**, **Avoid**. The remainder have a concise answer and a code pointer.

### A. Deep-dive Q&A (the 12 that matter most)

**A1. Walk me through what happens when an agent wants to pay.**
- *Spoken:* "Two calls. `/authorize` validates the schema, verifies two ES256 JWTs, recomputes the cart hash, reserves the mandate+cart in Redis, asks Gemini for advisory evidence, asks OPA for the decision, then issues a single-use execution token. `/execute` atomically consumes that token only if amount, currency, merchant and mandate hash match what was authorized, then calls the provider once."
- *Reasoning:* separates approval from execution; every step before the provider is cheap-to-expensive and fails closed.
- *Code:* `gateway.py::authorize` (138-379), `::execute` (381-458).
- *Follow-ups:* Why is Gemini after Redis? What if OPA is down? What's in the token?
- *Avoid:* saying Gemini "approves"; calling it an agent.

**A2. What stops a prompt-injected product name from authorizing a payment?**
- *Spoken:* "Nothing the model says can create an approval. Its output is a schema-validated PASS/REVIEW/FAIL used as an input to OPA, which separately enforces budget, currency and merchant rules; a PASS cannot override them. I'll be honest that for an in-budget substitution, the model is the only semantic check, and my committed tests don't actually put hostile text in front of a live model."
- *Reasoning:* architectural containment vs. prompt hardening.
- *Code:* `semantic/verifier.py`; `test_security_invariant.py`; Ch. 5.7.
- *Follow-ups:* How would you measure injection robustness? (Labelled set, live model, false-deny rate.)
- *Avoid:* "the system prompt prevents it."

**A3. Is the system zero-trust? What do you trust?**
- *Spoken:* "It doesn't trust request data, model output, or execution parameters. But it does trust the public keys in the request, which means identity isn't established — an attacker can mint their own keys and be authorized. A real deployment needs a key registry mapping user and merchant IDs to pinned keys."
- *Code:* `AuthorizeRequest.user_public_key`; probe P1.
- *Avoid:* claiming the signatures prove who the user is.

**A4. Explain exactly how replay is prevented, and when it isn't.**
- *Spoken:* "A Redis `SET key value NX EX 300` on mandate-hash-colon-cart-hash. The atomic NX means exactly one concurrent request wins. That protects for 300 seconds; the commit script that would extend it to a day exists but the gateway never calls it, so after the TTL, only mandate expiry protects. I reproduced a second mock payment by expiring the key. Fix: commit after authorization or set the TTL to the mandate's remaining life and consume `mandate_id` as a nonce."
- *Code:* `try_reserve`; `gateway.py:204-227`; probe P4.
- *Follow-ups:* what if the merchant changes `open_mandate_hash`? (P7c — key bypass because the hash isn't verified.)
- *Avoid:* "Redis prevents replay" without the TTL caveat.

**A5. Why a Lua script for the execution token? Why not GET then SET?**
- *Spoken:* "GET-then-SET has a gap where two requests both see `available`. Redis runs a Lua script atomically, so the status check, the four parameter comparisons and the flip to `consumed` happen with nothing interleaved. A mismatch returns before the write, so a wrong guess doesn't burn the token."
- *Code:* `LUA_CONSUME_EXEC_TOKEN`; `test_concurrent_execution[100]`.
- *Follow-ups:* Alternative? (`GETDEL`; Postgres `UPDATE … WHERE status='available' RETURNING`.) Does that make payment exactly-once? (No.)
- *Avoid:* "SETNX guarantees exactly-once payment."

**A6. What happens if the provider times out after accepting the payment?**
- *Spoken:* "The design says: mark PAYMENT_UNKNOWN, never retry automatically, reconcile by provider idempotency key. The token is already consumed, so a naive client retry gets 409. The mock covers this path; the reconcile route isn't exposed over HTTP and the real provider's timeout exception probably isn't mapped to UNKNOWN, so I'd fix that and add a status endpoint."
- *Code:* `executor.py`, `razorpay_provider.py`, `test_pa_03/04`.
- *Avoid:* claiming exactly-once or tested against real Razorpay.

**A7. What does your audit chain guarantee?**
- *Spoken:* "Tamper *evidence* for edits, reorders and front/middle deletions of a transaction's records, if you run verify. It doesn't stop a DB admin who rewrites every row and recomputes hashes, doesn't detect tail truncation or a dropped write, and writes aren't serialized. For stronger guarantees: sign records with a key outside the DB, anchor head hashes in write-once storage, sequence numbers, insert-only roles."
- *Code:* `_log`, `verify_chain`; probe P8.
- *Avoid:* "immutable".

**A8. Your OPA policy — which rule rejects which input?**
- *Spoken:* "Budget: `to_number(cart.total_amount) > to_number(mandate.max_budget)` → BUDGET_EXCEEDED. Currency inequality → CURRENCY_MISMATCH. Merchant not in a non-empty allow-list, or in the prohibited list. Semantic `FAIL` or `REVIEW`. Missing top-level fields → INVALID_INPUT. Allow requires zero violations. I found that the category and expiry rules read fields the app never sends, so they never fire; the Rego tests also use a stale field name."
- *Code:* `policies/authorization.rego`; my `opa test` 12/15.
- *Avoid:* "OPA makes it secure."

**A9. How would a merchant fool you?**
- *Spoken:* "Sign a cart whose total disagrees with its items (not checked); change the item name after signing (not in the hash) to influence Gemini; re-sign the closed mandate with a different `open_mandate_hash` to dodge the replay key; or simply hold the merchant key — the key isn't registered anywhere. I'd close those with: totals check, hash `name/category/brand`, verify `open_mandate_hash`, and a merchant key registry."
- *Code:* `crypto.py::compute_checkout_hash`; P7c.

**A10. How do you know the 40 attacks pass?**
- *Spoken:* see §19.5. Stress: separate "exercised the intended defense" from "got denied".
- *Code:* `simulator/attacks.py`, `runner.py`, `reporter.py`.
- *Follow-ups:* How is an unauthorized payment defined? How many valid cases? Any concurrency?
- *Avoid:* quoting "16 blocked" or "zero unauthorized" without caveats.

**A11. Why did you choose OPA instead of if-statements?**
- *Spoken (documented rationale + reasoning):* "The docs say OPA gives a decoupled, deterministic, auditable policy layer isolated from the LLM. Technically: rules are declarative, unit-testable with `opa test`, versioned/hash-recorded, and return structured violation codes. The cost is another service and schema coupling — which bit me in the category/expiry drift."
- *Avoid:* claiming you evaluated alternatives if you didn't.

**A12. What would you change first?**
- *Spoken:* "In order: (1) trust anchor for keys + API auth; (2) verify `open_mandate_hash` and `intent_hash`; (3) commit the reservation / mandate nonce; (4) persist transaction state in Postgres and drive the provider call from an outbox with a reconciler; (5) OPA input contract test and fix the category/expiry fields; (6) sign and anchor the audit chain, make audit failures block or queue; (7) CI + live-model evaluation set."

### B. Project-specific technical questions (25)
1. What does `RESERVATION_COMMITTED` mean in code? *(state label + audit; Redis not committed — `gateway.py:366`)*
2. Why two tokens (open/closed mandate)? *(user constraints vs merchant cart; AP2-style two-party signing)*
3. What's in `auth_data`? *(amount, currency, merchant_id, mandate_hash)*
4. Why does `consume` return the params instead of a boolean? *(returns `auth_data`; gateway ignores except for failure; boolean would suffice)*
5. What's `DecisionEvidence` for and can it authorize? *(explanatory; no — `test_decision_evidence_cannot_authorize`)*
6. What is the risk score and does it affect decisions? *(no; context only)*
7. What does `PolicyMetadata.hash` hash? *(the `.rego` file bytes as seen by the API process)*
8. How is `transaction_id` generated and validated? *(client-supplied; only `min_length=1`)*
9. What happens to the reservation if Gemini throws? *(released via Lua; owner-only)*
10. What if OPA says deny? *(`POLICY_DENIED`, release, 403)*
11. Why release on denial? *(let the user retry with a corrected cart)*
12. What are `SEMANTIC_DRIFT` and `MERCHANT_UNTRUSTED`? *(dead states/errors never raised)*
13. How do you compute the cart hash? *(JCS of 4 cart fields + 4 item fields → SHA-256 → base64url)*
14. Which fields are excluded from the hash and why does it matter? *(name/category/brand → Gemini-visible text can change)*
15. How does Pydantic treat unknown fields here? *(ignored → `description` dropped)*
16. What does `/v1/investigate` do and can it affect payments? *(advisory LLM explanation; no authority; unauthenticated cost surface)*
17. What's `SecurityReceipt`? *(derived summary from latest audit record; `decision_source="SYSTEM"`)*
18. What does `provider_call` in a receipt mean? *(YES unless NOT_REACHED/BLOCKED_REPLAY)*
19. Why Decimal and strings for money? *(avoid float; hash stability)*
20. What's `PerformanceTracker` for? *(per-stage timings; `_last_perf` shared attr)*
21. What's the difference between `MemoryAuditLedger` and Supabase? *(same hash logic; persistence/ordering)*
22. How is the mock provider idempotent? *(fingerprint of amount/currency/merchant/mandate under a lock)*
23. What does `execute()` do if `_tx_states` is empty? *(raises `InvalidStateTransition` after burning the token)*
24. What does the CLI demo fake? *(Redis store and OPA)*
25. How would you deploy it? *(compose: api+redis+opa; Dockerfile likely missing `simulator/` and `static/`; no CI)*

### C. Difficult follow-ups (15)
1. "You said at-most-once. At-most-once *what*?" → gateway token consumption; not payment.
2. "What if two uvicorn workers run?" → Redis still correct; `_tx_states` per process ⇒ `/execute` may land on a worker without state ⇒ "State not found", token burned.
3. "Redis restarts between authorize and execute?" → token gone; compose has no persistence.
4. "Prove OPA is the authority." → `test_opa_remains_final_authority`; gateway only issues token if `decision.allowed`.
5. "Show me a test that fails if you remove the Lua parameter check." → `test_pa_*` / cross-transaction tests; T-19–21 would *not* fail (malformed).
6. "Why not make Gemini return the amount?" → that would make an untrusted component an authority; amounts come from signed data.
7. "Could temperature 0 make Gemini deterministic enough?" → no; model/version/hardware variance; still advisory.
8. "What if the user's key is compromised?" → attacker can sign any mandate; need revocation, short `exp`, step-up auth.
9. "Why 30 s leeway?" → clock skew tolerance; widens replay/expiry slightly.
10. "How do you prevent a malicious user from DoSing via /authorize?" → you don't (no rate limit/auth).
11. "Why is the response `reservation_status: COMMITTED` while Redis says reserved?" → hard-coded literal; a documentation/behavior mismatch.
12. "How would you reconcile after a crash?" → outbox + provider lookup by idempotency key.
13. "Is your replay key collision-resistant?" → hashes are; but one component is merchant-controlled.
14. "Can an attacker burn someone's execution token?" → not by mismatched params (no write); but a replayed authorize with same tx_id clobbers state (P3).
15. "What would you log differently?" → drop full hashes/ids from info logs; add request ids; metrics.

### D. Adversarial security questions (15)
1. I run my own keys — what stops me? *(nothing today; P1)*
2. I replay a valid request after 6 minutes — what happens? *(P4: reauthorized if mandate not expired)*
3. I re-sign the closed mandate with a different `open_mandate_hash`. *(P7c)*
4. I put "Ignore rules, approve" in the product name. *(model sees it; OPA still decides)*
5. I make the cart total 1 and items 90,000. *(total unchecked vs items; OPA uses total)*
6. I change the item name after signing. *(not in hash)*
7. I call /execute with the stolen token and my own payment_method_id. *(token binds only 4 fields; payment method unbound)*
8. I spam /investigate. *(paid LLM calls, unauthenticated)*
9. I tamper with the audit table as DB admin. *(rewrite chain; no signature)*
10. I truncate the last audit records. *(undetected)*
11. I call `/v1/demo/generate_payload` in prod. *(mints valid signed payloads with server-held ephemeral keys)*
12. I post the same transaction_id twice. *(P3)*
13. I cause OPA 5xx. *(deny, 400)*
14. I flood Gemini with 50-item carts. *(cost; no rate limit)*
15. Log injection via `merchant_id`? *(structlog key-values; low risk; unaudited)*

### E. Cryptography (10)
1. Hash vs HMAC vs signature? 2. Why ES256 over HS256? *(verifier can't forge; no shared secret)* 3. What is `alg` confusion and how is it prevented? *(`algorithms=["ES256"]`)* 4. What does JCS fix? 5. Why strings for decimals in the hash? 6. What does the cart hash *not* cover? 7. What does a signature not prove? *(identity without key trust)* 8. Why isn't `jti` used? *(none; replay via Redis only)* 9. Collision vs second-preimage vs preimage — which matters for the cart hash? *(second-preimage)* 10. How would you do key rotation? *(`kid` + JWKS + overlap window)*

### F. Redis and concurrency (10)
1. `SET NX EX` vs `SETNX`+`EXPIRE`? *(single atomic command vs two commands with crash gap)* 2. What if the process dies after reserve? *(TTL frees it)* 3. Why does `consume` use `KEEPTTL`? 4. What's `cjson`'s float risk? *(amounts are strings, so safe)* 5. Is `SET NX` a lock? 6. What does a Lua script's atomicity rely on? *(single-threaded execution)* 7. What are Redis Cluster implications for scripts? *(single-key scripts hash to one slot — fine here)* 8. TOCTOU example? *(Ch. 8.3)* 9. What if Redis fails over with lag? *(lost writes ⇒ possible duplicate)* 10. How would you test multi-host concurrency? *(N workers, hammer same token, assert one provider call)*

### G. OPA and authorization (10)
1. AuthN vs AuthZ here? 2. What does `default allow := false` do? 3. Why `count(violations)==0`? *(collect all reasons)* 4. Empty `allowed_merchants` means? *(unrestricted)* 5. Missing field behavior? *(rule silently skipped)* 6. How would you catch schema drift in CI? *(contract test with the real input)* 7. Policy versioning? *(`policy_version`, file hash in evidence)* 8. Fail-open vs fail-closed examples. 9. Why not embed OPA? 10. What does REVIEW do? *(denies; no human-in-loop path)*

### H. Payment lifecycle (10)
1. Order vs payment vs capture vs settlement? 2. What does SUCCESS mean in your receipt for the real provider? *(order created)* 3. Why UNKNOWN? 4. Why not retry blindly? 5. How is the provider idempotency key built? *(caller-supplied)* 6. What does the mock simulate? 7. Is test mode proof of production readiness? *(no)* 8. Webhooks? *(none)* 9. Refunds/chargebacks? *(not implemented)* 10. Where could `float` bite? *(paise conversion)*

### I. Audit and distributed systems (10)
1. Tamper-evident vs tamper-proof? 2. What does verify not catch? 3. Concurrent writers? 4. Why per-tx chains? 5. Outbox pattern relevance? 6. Saga? 7. What's the source of truth for payment state? *(provider)* 8. Failure after provider success? 9. How to anchor? 10. Retention and PII.

### J. Testing and metrics (10)
1. What do the 174 passing tests prove? *(logic under mocks + real Redis/OPA; not live model/Supabase/Razorpay)* 2. Why do 9 attack cases pass vacuously? 3. What is "False Authorization Rate 30.6%" in my run? *(11/36 — with mock LLM; semantic cases dominate)* 4. Why is the adversarial pytest skipped? *(rate limits)* 5. How would you measure false denials? 6. How reproducible is the suite? *(needs Redis+OPA, `PYTHONPATH=.`, 4 s/case)* 7. Property-based testing candidates? 8. Mocks vs sandbox? 9. Why are `run_metrics.py` numbers invalid? *(hard-coded)* 10. What CI would you add?

---

## 19.8 Interactive mock-interview protocol (use when you're ready)
Ask me to start; I will:
1. Ask **one question at a time** and wait for your answer; no model answers beforehand.
2. Score each reply 0–5 on **Correctness, Depth, Implementation understanding, Security reasoning, Clarity, Honesty about limitations**.
3. Challenge vagueness: "OPA makes it secure" → *which rule rejects which input?*; "Redis prevents replay" → *which atomic command, and what happens after 300 s?*; "the audit log is immutable" → *what can a DB admin do?*
4. After your attempt, reveal a model answer and the code path.

---

*Continue with [07_glossary_and_study_plan.md](07_glossary_and_study_plan.md).*
