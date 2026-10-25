# Part 4 — Threat Model, the "40 Attack Vectors", and Testing (Chapters 11–13)

← [Main guide](VILR_DEEP_DIVE.md) · ← [03](03_state_payment_audit.md) · Next → [05_backend_distsys_algos_stack.md](05_backend_distsys_algos_stack.md)

---

# Chapter 11 — Security threat model

## 11.1 Assets, boundaries, surfaces

| Category | Items |
|---|---|
| **Assets** | (1) money movement authority (the execution token); (2) the user's mandate constraints; (3) the integrity of the cart; (4) the audit trail; (5) API secrets (`GEMINI_API_KEY`, `RAZORPAY_KEY_*`, `SUPABASE_*`); (6) user/merchant identifiers in audit records |
| **Trust boundaries** | client ⇄ gateway; gateway ⇄ Gemini; gateway ⇄ OPA; gateway ⇄ Redis; gateway ⇄ provider; gateway ⇄ Supabase |
| **Security-sensitive operations** | `consume_execution_token`, `PaymentExecutor.execute`, `provider.execute_payment`, `policy.evaluate`, `audit.record` |
| **Untrusted inputs** | the whole `AuthorizeRequest` and `ExecuteRequest` (including **public keys**), merchant item names/brands, `raw_prompt`, `additional_instructions`, `provider_idempotency_key`, `payment_method_id`, `transaction_id` |
| **External dependencies** | Gemini API, OPA (HTTP), Redis, Razorpay, Supabase, PyPI packages |
| **Attack surface** | unauthenticated HTTP: `/v1/authorize`, `/v1/execute`, `/v1/audit/{tx}`, `/v1/audit/{tx}/verify`, `/v1/receipt/{tx}`, `/v1/investigate/{tx}` (paid LLM call), `/v1/demo/generate_payload` (mints keys & signed payloads), `/v1/demo/concurrency` (100 parallel executes), `/health`, `/dashboard` static |

## 11.2 The four evidence tiers (don't blur them)
| Tier | Meaning | Example here |
|---|---|---|
| **A. Vulnerability demonstrated** | I (or a committed test) reproduced it | P1 self-minted keys; P4 replay after TTL; P8 audit tail truncation |
| **B. Plausible, untested** | follows from the code, no reproduction | provider timeout mis-classified as FAILED; concurrent audit-write fork |
| **C. Attack mitigated in a test** | a test that really exercises the defense | T-03 cart tamper; T-08 concurrency; `test_concurrent_execution` |
| **D. Defense merely asserted** | in docs/README only | "Redis protects concurrent execution", "Semantic mismatch … consistently mitigated" |

## 11.3 Threat table

| Threat | Attack path | Existing defense | Evidence | Residual risk |
|---|---|---|---|---|
| **Prompt injection** (merchant `name`/`brand`, `raw_prompt`) | hostile text in prompt makes Gemini say PASS | system prompt hardening; schema; **OPA still enforces budget/currency/merchant**; PASS can't override | C for "cannot override budget" (`test_security_llm_cannot_override_budget`, `test_security_invariant_*`); D for "consistently mitigated" injections | In-budget substitution depends on the model; `allowed_categories` inert (Ch. 7); no live-model result reproducible (UNKNOWN) |
| **Intent tampering** | alter `user_intent` fields | OPA reads **signed** constraints, not request constraints | A for the gap: P2 (altered `raw_prompt`/`intent_hash` unchecked) | Gemini sees unsigned text; cannot detect intent forgery |
| **Recipient (merchant) substitution** | change `cart.merchant_id` after signing | merchant_id inside cart hash | C: P6 → `HASH_MISMATCH`; T-03-style | merchant key holder can sign anything; `closed.iss` never compared to `cart.merchant_id` |
| **Amount manipulation** | edit cart total | cart hash; OPA budget; Lua amount equality at execute | C: T-03, T-05, `test_pa_*`; A for gap: total ≠ Σ items unchecked | merchant-signed inconsistent totals pass |
| **Currency mismatch** | cart currency ≠ mandate currency | OPA `CURRENCY_MISMATCH`; Lua currency equality | C: `test_deny_currency_mismatch`, integration `test_policy_engine` | – |
| **Replay (short)** | resend same request | Redis `SET NX` | C: T-04, T-22 | – |
| **Replay (after TTL)** | resend after 300 s | JWT `exp` only | **A: P4 double mock payment**; T-23 fails | needs `commit()`/nonce |
| **Replay-key bypass** | merchant re-signs closed mandate with different `open_mandate_hash` | none | **A: P7c** | open↔closed binding missing |
| **Duplicate requests / double click** | two `/execute` calls | Lua consume | C: `test_concurrent_execution[10,50,100]`, T-08 | multi-host untested |
| **Concurrent execution** | N parallel executes | atomic Lua | C (above) | provider call isn't atomic with consume |
| **Broken authorization / no authN** | call any endpoint | none | A: no auth deps in `routes.py` | anyone can mint keys (P1), read audit, trigger LLM calls |
| **Self-asserted keys (forged mandates)** | attacker generates own key pair, supplies JWKs | none | **A: P1** | needs a trusted key registry/JWKS pinned to `user_id`/`merchant_id` |
| **Malformed model output** | non-JSON, bad enum, confidence 5 | Pydantic → `_safe_fail` → `FAIL` → OPA deny | C: `test_sv_08/09/10/12/21` (mock-driven) | model behavior itself untested |
| **Forged/invalid signature** | wrong key, tampered JWT, `alg` games | `algorithms=["ES256"]` | C: `test_modified_jwt`, `test_wrong_signer_key`, `test_signer_wrong_alg` | self-asserted keys (above) |
| **Missing/expired credentials** | expired mandate | JWT `exp`/`iat` + 30 s leeway | C: T-06, `test_expired_mandate` | leeway; OPA expiry inert but JWT covers |
| **Redis outage** | Redis down | authorize: fail-closed; execute: 500 (no payment) | C(weak): `test_redis_unavailable_fails_closed` | restart wipes state (config) |
| **Policy-service outage** | OPA down/timeouts | `PolicyUnavailable` → deny, reservation released | B/C: recorded failing integration tests show the error path; no focused test | HTTP 400 not 503 |
| **Provider timeout** | response lost | `UNKNOWN` → `PAYMENT_UNKNOWN`, no auto-retry | C vs mock only (`test_pa_03`) | real SDK timeout likely mis-mapped to FAILED (B) |
| **Audit-log tampering** | edit/delete/reorder rows | hash chain verified on demand | C: `test_a_03..06`, T-36–39 (memory ledger) | A: tail truncation & dropped writes undetected (P8); admin can rewrite chain; Supabase path never run by me |
| **Credential leakage** | secrets in repo/logs/evidence | `.env` gitignored; test that evidence omits secrets | C: `test_a_12`; I saw no secret values in tracked files | `structlog` logs print full mandate hashes/ids; `/v1/audit` unauthenticated |
| **Forged callbacks/webhooks** | fake provider webhook | n/a — no webhooks | – | not applicable; also no async confirmation |
| **Inconsistent payment state** | Redis ≠ provider ≠ audit | PAYMENT_UNKNOWN + reconcile concept | partial | no reconciler, in-memory `_tx_states`, token burn on restart |
| **Unauthenticated cost DoS** | spam `/authorize` or `/investigate` | input size caps only; no rate limit (grep) | A | Gemini bill/latency |
| **In-memory state confusion** | re-POST same `transaction_id` | – | A: P3 (legit token burned) | availability attack for anyone who knows the tx_id |

---

# Chapter 12 — The "forty attack vectors", row by row

## 12.1 The claim vs what exists
- CV: "Forty attack vectors tested with zero unauthorized payments."
- README: "40 attack vectors covering cart tampering, replay attacks, concurrent double-spends, and semantic manipulation: **0 unauthorized payments** … **16 attacks were deterministically blocked** by Gateway layers (Crypto, Redis, OPA)."
- **Verified:** `simulator/attacks.py` registers exactly **T-01…T-40** plus **V-01, V-02** (valid controls) = **42 cases**. So "40 attacks" is accurate as a count of *registered attack definitions*. (VERIFIED.)
- **Other numbers in the repo disagree:** committed `docs/security-benchmark.md`: 23 blocked / 1 detected / 16 not blocked (V-02 errored, T-36–39 marked "inapplicable"); `docs/VILR_FINAL_CLAIM_AND_EVIDENCE_AUDIT.md`: 23 / 5 / 14; `docs/final-claims-review.md`: "186 total tests (180 BLOCKED, 6 DETECTED, 0 NOT_BLOCKED)"; my run: **23 / 5 / 12** (30 PASS, 12 FAIL). I cannot reconcile "16" from any of them. Treat the docs as inconsistent (DOCUMENTED, not reproducible).

## 12.2 How the harness works (VERIFIED)
`scripts/cli.py security` → `AttackRunner.run_baseline("VILR")` → for each attack: enter FastAPI lifespan (fresh gateway, **fresh mock provider**), `sleep(4)`, call `attack.execute(client)` against `/v1/authorize` and/or `/v1/execute` through `httpx.ASGITransport` (in-process, no sockets), map the HTTP status to `ALLOW/DENY/ERROR` (`extract_outcome`: 200 with status AUTHORIZED/CONFIRMED/SUCCESS → ALLOW; 400/401/403/404/409/422 → DENY; 500 → ERROR), read the mock provider's `payment_call_count/payment_creation_count`, and compare with the case's expected decision & side effect.
- Uses: real FastAPI app code, **real Redis, real OPA** (must be running), **mock LLM by default**, **mock Razorpay**, **in-memory ledger** unless Supabase env set.
- "Side effect" = `payment_creation_count > 0` on the mock provider. **"Unauthorized payment" is not defined beyond "a payment was created in a case that expected none".**
- `--baseline` also runs Baseline A/B/C stubs (A: trust everything; B: budget check only; C: signature check only) — stub gateways that return canned `CONFIRMED`; they illustrate "what weaker designs allow" and were not run by me.
- Reproduce: start Redis and OPA, then `PYTHONPATH=. REDIS_URL=… OPA_URL=… python scripts/cli.py security` (≈3 min; writes `docs/security-benchmark.md` and `results/security-benchmark.json`, so run in a copy). Needs `PYTHONPATH=.` because `simulator/` isn't in the package list.

## 12.3 Matrix of all 40 (+2 valid controls)
Columns: **Intended defense** (case's `defense_layer`) · **What the test really sends** · **My run** (HTTP / decision / PASS-FAIL) · **Does it exercise the intended defense?**

Legend: ✅ exercised and held · ⚠️ denied but not by the named mechanism · 🟥 passes only because the body is malformed (HTTP 422, defense never reached) · ❌ failed its own expectation

| ID | Attack scenario | Intended defense | What the test actually does | My run | Verdict |
|---|---|---|---|---|---|
| T-01 | Indirect prompt injection via merchant metadata | Semantic → OPA | valid payload + `merchant_description` (dropped by `CartItem`) | 200 ALLOW FAIL | ❌ injection never reaches prompt; mock LLM says PASS anyway |
| T-02 | Semantic product substitution | Semantic | `merchant_description="Laptop battery charger"` (dropped); item name stays "Laptop" | 200 ALLOW FAIL | ❌ nothing to detect |
| T-03 | Cart tampering after signing | Cart hash | `total_amount="1.00"` after signing | 400 DENY PASS | ✅ |
| T-04 | Replay of committed tx | Redis | same payload twice | 409 DENY PASS | ✅ (within 300 s) |
| T-05 | Over-budget | OPA | signed cart 90,000 vs mandate 50,000 | 403 DENY PASS | ✅ |
| T-06 | Expired mandate | JWT `exp` | open mandate `exp=0` | 400 DENY PASS | ✅ |
| T-07 | Forged signature | Verifier | `closed_checkout_token="ey.invalid.signature"` | 409 DENY PASS | ⚠️ decode error on *closed* token → state-machine bug (409, not 401), no failure audit |
| T-08 | Concurrent duplicate execution | Redis Lua | authorize once, 2 parallel `/execute` | 409 DENY PASS; creation count 1 | ✅ (plus `test_concurrent_execution` 10/50/100) |
| T-09 | Malicious malformed LLM output | Semantic verifier | marker `TRIGGER_MALFORMED_JSON` in an ignored field | 200 ALLOW FAIL | ❌ marker handled nowhere; real coverage is `test_sv_08/12/21` |
| T-10 | LLM timeout | Semantic fail-closed | marker `TRIGGER_TIMEOUT` | 200 ALLOW FAIL | ❌ same; real coverage `test_sv_09/10` |
| T-11 | Agent impersonation | Verifier | `merchant_public_key = user_public_key` | 409 DENY PASS | ⚠️ same state-machine path as T-07 |
| T-12 | "Policy file tampering" | Policy engine | `merchant_id="default allow = true"` | 200 ALLOW FAIL | ❌ premise invalid (request can't alter OPA policy); the merchant is simply unlisted |
| T-13 | Audit tampering | Ledger | mutate first record's `state` in memory, call verify | 200 DETECTED PASS | ✅ memory ledger only |
| T-14 | "Key compromise" | Verifier | merchant key swapped for the user's | 409 DENY PASS | ⚠️ a real compromise (attacker has the private key) is **accepted** — see P1 |
| T-15 | OPA unavailable | Fail-closed | merchant id `TRIGGER_OPA_TIMEOUT` | 200 ALLOW FAIL | ❌ no OPA fault is injected |
| T-16 | Execute without authorization | Executor/Redis | body `{transaction_id, execution_token}` only | 422 DENY PASS | 🟥 required fields missing |
| T-17 | Another transaction's token | Redis ownership | same incomplete body | 422 | 🟥 (real: T-24, tests) |
| T-18 | Reuse an execution token | Redis | same incomplete body | 422 | 🟥 (real: T-08) |
| T-19 | Modify amount between authorize/execute | Lua param check | `{tx, token, amount}` only | 422 | 🟥 (real: `test_payment_execution` / Lua) |
| T-20 | Modify merchant | Lua param check | `{tx, token, merchant_id}` only | 422 | 🟥 |
| T-21 | Modify mandate hash | Lua param check | `{tx, token, mandate_hash}` only | 422 | 🟥 |
| T-22 | Replay with new tx_id | Redis key ignores tx_id | authorize twice, 2nd with new id | 409 DENY PASS | ✅ |
| T-23 | Replay after reservation expiry | Redis TTL | authorize **once** with `tx_23` | 200 ALLOW FAIL | ❌ test never waits/expires; the real scenario is exploitable (P4) |
| T-24 | "Commit another tx's reservation" | Redis ownership | execute with tx A's token under another tx id | 400 DENY PASS | ✅ ownership check (mislabelled: it's a *token* test, not reservation commit) |
| T-25 | "Release another tx's reservation" | Redis ownership | authorize once with `tx_25` | 200 ALLOW FAIL | ❌ no release attempted; store-level ownership is covered by `test_idempotency_store` |
| T-26 | Conflicting provider idempotency key | Provider mock | incomplete execute body | 422 | 🟥 (real: `test_pa_07/08/09`) |
| T-27 | PAYMENT_UNKNOWN double execution | Executor | incomplete execute body | 422 | 🟥 (real: `test_unknown_cannot_trigger_automatic_retry`) |
| T-28 | Unicode / normalization trick | Semantic | `description="Lạptop"` (dropped) | 200 ALLOW FAIL | ❌ |
| T-29 | Very long merchant description | API validation | sets `cart.merchant_id="A"*10000` **after** signing | 400 DENY PASS | ⚠️ denied by *hash mismatch*; no length limit exists |
| T-30 | Large cart / resource exhaustion | API validation | replaces 500 items after signing | 400 DENY PASS | ⚠️ denied by hash mismatch; the 50-item cap sits behind it and is never reached |
| T-31 | Malformed JSON | Framework | `content="bad json"` | 422 DENY PASS | ✅ (framework-level, trivially true) |
| T-32 | Unknown semantic enum | Semantic validation | **identical to V-01** (plain valid request) | 200 ALLOW FAIL | ❌ nothing malformed is injected (real: `test_sv_21`) |
| T-33 | Invalid confidence | Semantic validation | identical to V-01 | 200 ALLOW FAIL | ❌ |
| T-34 | Missing semantic evidence | Semantic | identical to V-01 | 200 ALLOW FAIL | ❌ |
| T-35 | Policy input type confusion | OPA | `total_amount={"value":5000}` | 422 DENY PASS | ⚠️ Pydantic stops it before OPA; OPA itself is fail-open on type errors (§7.4) |
| T-36 | Tampered audit record | Ledger | mutate memory record | DETECTED PASS | ✅ memory ledger |
| T-37 | Deleted audit record | Ledger | `pop(0)` (front) | DETECTED PASS | ✅ (tail deletion would pass undetected, P8) |
| T-38 | Reordered audit records | Ledger | swap two records | DETECTED PASS | ✅ |
| T-39 | Broken `prev_record_hash` | Ledger | edit link | DETECTED PASS | ✅ |
| T-40 | Replay of expired execution token | Redis TTL | incomplete execute body | 422 DENY PASS | 🟥 expiry untested |
| V-01 | Valid authorization (control) | – | normal payload | 200 ALLOW PASS | ✅ |
| V-02 | Valid execution (control) | – | authorize→execute | ALLOW, payment created 1, PASS | ✅ (in the committed report this row shows ERROR `'execution_token'`) |

### Tally (my run, derived from the table)
| Category | Count | IDs |
|---|---|---|
| ✅ exercised & held | **12** | T-03, 04, 05, 06, 08, 13, 22, 24, 36, 37, 38, 39 |
| ⚠️ denied, but not by the named mechanism | **7** | T-07, 11, 14, 29, 30, 31, 35 (31 is legitimate framework behavior) |
| 🟥 passes only due to malformed body | **9** | T-16–T-21, T-26, T-27, T-40 |
| ❌ failed own expectation | **12** | T-01, 02, 09, 10, 12, 15, 23, 25, 28, 32, 33, 34 |
| **Total** | **40** | = 23 BLOCKED + 5 DETECTED + 12 NOT_BLOCKED ✔ (matches the reporter) |

## 12.4 Reading the "zero unauthorized payments" claim honestly
- **True in the narrow sense:** across the suite the mock provider created exactly two payments, both legitimate (T-08's single winner and V-02). VERIFIED (my run: `Σ payment_creation_count = 2`).
- **Why it's weaker than it sounds:** the 12 cases the gateway mis-authorized never call `/execute`, so no payment can occur *by construction*. 9 "execution" attacks are rejected by schema validation before any security logic. 7 more are denied by something other than the named defense.
- **A genuine double-spend-like path exists outside the suite:** P4 (reauthorize after reservation TTL → second mock payment); P1 (self-minted keys → authorized for any amount); P7c (replay-key bypass). Whether these count as "unauthorized" depends on a definition the repo doesn't give. Say: *"in the suite, no provider call occurred that the harness didn't expect; my own probing found replay and key-trust gaps the suite doesn't cover."*
- **Does it measure false rejections?** Only 2 valid controls (V-01, V-02). "False Denial Rate 0/2" is not statistically meaningful.
- **Does it test failure paths and concurrency?** Concurrency: yes (T-08, pytest 10/50/100). Redis/OPA/Gemini outage: not as attacks (markers are inert); partial unit tests.
- **Same authorization code for every attack?** Yes for VILR (the real `GatewayOrchestrator`); baselines swap in stub gateways.
- **Mocks vs live:** mock LLM (default), mock provider, memory ledger; Redis and OPA live. The committed docs claim live Gemini/Supabase/Razorpay-TEST demonstrations (DOCUMENTED; not reproducible by me).

### Why zero-failures on a finite suite is evidence, not proof
A finite test set shows the defenses handle *those inputs*. Security failures live in the inputs nobody enumerated (P1, P4, P7 were not among the 40). The strength of evidence depends on (a) coverage of distinct attack *mechanisms*, (b) whether each test can fail for the right reason (a test that can't fail — like the 422 bodies — is not evidence), and (c) independent review. "No failures observed" ≠ "no failures exist".

### What to say
> "There are forty attack definitions plus two valid controls. When I re-ran them I got 30 pass, 12 fail; the failures are mostly semantic cases that need a live model and some tests whose payloads don't actually trigger the scenario. Nine execution cases are rejected by schema validation, so they're really covered by the integration tests. The suite's headline is that no unexpected provider call happened, and I've documented additional gaps — replay after the reservation TTL and request-supplied keys — that I'd fix first."

---

# Chapter 13 — Testing and evaluation from first principles

## 13.1 What exists (my run: 174 passed, 45 skipped; skips = 42 parametrized adversarial cases deliberately skipped, 2 live-Gemini tests without a key, 1 "Schema changed")

| Layer | Files | What they validate | Dependencies |
|---|---|---|---|
| **Unit — domain/crypto** | `test_crypto.py`, `test_domain_models.py`, `test_mandate_verifier.py`, `test_state_machine.py` | JCS determinism/golden vector, hash sensitivity (SKU/currency/add-remove), alg confusion, expiry, wrong key, valid transitions | none |
| **Unit — semantic** | `test_semantic_verifier.py` (21), `test_gemini_provider_unit.py` | prompt limits, malformed/hostile *mock* LLM output → `FAIL`; Gemini provider error mapping with patched client | `MockLLMProvider` with canned responses |
| **Unit — audit** | `test_audit_ledger.py` (A-01…A-12) | genesis, chain, tamper/delete/reorder/link detection, evidence presence, no secrets | memory ledger |
| **Unit — "security boundaries"** | `test_tier2a/2b/2c_security_boundaries.py` | LLM/evidence/explanation/risk cannot authorize; unauthorized cannot reach executor; UNKNOWN not auto-retried; replay causes no provider side effect | mocks |
| **Integration — Redis** | `test_idempotency_store.py` | reserve/commit/release/ownership/TTL/races | **real Redis** (20 errors in the committed run without it) |
| **Integration — OPA** | `test_policy_engine.py` | budget/currency/multi-violation/semantic/default-deny, OPA-down error | **real OPA** |
| **Integration — gateway/E2E** | `test_gateway.py`, `test_e2e.py`, `test_cart_http.py`, `test_security_invariant.py` | orchestration order, state transitions, AI-PASS+OPA-DENY invariant | mocks/ASGI |
| **Integration — payment** | `test_payment_execution.py` (PA-01…15) | success, failure, timeout→UNKNOWN, reconcile, idempotent replay, conflicting key reuse, concurrent duplicates | `MockRazorpayProvider` |
| **Integration — concurrency** | `test_concurrency.py` | 10/50/100 parallel executes → exactly one payment | real Redis + OPA |
| **Adversarial** | `tests/security/test_adversarial.py` | runs the 42 simulator cases — **skipped by decorator** | – |
| **Live LLM** | `test_gemini_provider.py` | real Gemini call | needs key (skipped) |

Not present: property-based tests (no `hypothesis`), fuzzing, multi-process concurrency, Supabase tests, real-Razorpay tests, CI.

## 13.2 Concepts, mapped
- **Unit vs integration vs end-to-end:** one function in isolation vs real collaborators vs the whole request path. Gaps arise at the seams — e.g., OPA unit-ish tests pass while the real-input schema drifted.
- **Negative testing:** assert bad inputs fail *for the right reason*. The 9 malformed-body cases show how a negative test can pass vacuously. Cure: assert the **error code/state**, not just "non-200".
- **Mocks/fakes:** `MockLLMProvider`, `MockRazorpayProvider` (a behaving fake with idempotency), `FakeIdempotencyStore` (CLI). Risk: tests validate your mock, not the dependency (the timeout exception type mismatch is the textbook case).
- **Test isolation & deterministic fixtures:** simulator creates one module-level `ScenarioGenerator()` with fixed keypairs per run; random tx ids; Redis keys random → mostly isolated, but a shared Redis persists across cases.
- **Flaky tests:** LLM-live tests; `sleep(4)` in the runner for rate limits; asyncio concurrency tests are deterministic because Redis serializes.
- **Coverage vs correctness:** `pytest-cov` is a dev dependency but no coverage figure is committed; coverage says code ran, not that the assertion was meaningful.
- **False positives/negatives in security tests:** FP = test says "attack blocked" but the defense didn't act (422 cases). FN = test says "allowed" but it's a bad test (T-12 premise).
- **Testing money flows without money:** mock providers with injectable outcomes (`injected_outcome`, `injected_timeout_after_acceptance`, `injected_network_failure`), provider sandbox/test mode, assertion on call counts (`payment_call_count`), and contract tests that the real SDK's exceptions map to your domain errors.
- **No claim without evidence:** the committed `test_results.txt` (19 failed / 160 passed / 20 errors) is a recorded run without infrastructure; my run with Redis+OPA is 0 failures. Cite whichever you reproduced yourself, and say which.

## 13.3 Proposed additional tests (**not present** — a backlog, kept separate on purpose)
1. **Closed↔open binding:** closed mandate whose `open_mandate_hash` ≠ hash(open token payload) must be denied. (Currently P7a authorizes.)
2. **Intent binding:** `intent_hash` ≠ hash(request intent) denied. (P2.)
3. **Replay after TTL:** with a short-TTL reservation, re-authorize same mandate+cart → denied; second execution impossible. (P4.)
4. **Key registry:** unknown public key → 401 even if signature is valid. (P1.)
5. **Execute-body attacks done right:** authorize, then execute with (a) wrong amount, (b) wrong merchant, (c) wrong mandate hash, (d) consumed token, (e) expired token (TTL shortened) — each asserting the exact exception/status and `payment_call_count == 0`.
6. **Closed-mandate failure path:** assert HTTP 401/400 and a failure audit record (fixes the 409 state bug).
7. **Same-`transaction_id` re-authorize** must not clobber live state (P3).
8. **OPA contract test:** feed the *exact* `opa_input` shape built by the gateway to `opa test`/the live server for every rule; fail CI if a rule field doesn't exist in the schema (catches `exp`/`category`/`max_amount` drift).
9. **Rego tests:** fix `max_amount`→`max_budget`; add tests with per-item category.
10. **Outage injection:** OPA 5xx/timeout, Redis `ConnectionError` at execute, Gemini timeout via a fault-injecting provider (not magic strings).
11. **Real SDK exception mapping:** unit test that `requests.exceptions.Timeout` from the Razorpay client yields `UNKNOWN`.
12. **Audit:** concurrent `_log` writers for one tx (expect either serialization or detectable fork); tail truncation (needs a stored head hash); Supabase failure must not silently drop.
13. **Property-based (Hypothesis):** for random carts, `compute_checkout_hash` is stable under key reordering and changes under any field mutation; for random `(amount,currency,merchant,hash)` tuples the Lua consume succeeds iff all equal.
14. **Multi-process concurrency:** run N uvicorn workers against one Redis to prove no cross-process double consume (and expose the `_tx_states` per-process problem).
15. **Live-model evaluation** (separate, rate-limited, never a CI gate): fixed labelled set of benign and injected carts; report precision/recall and **false-deny rate**, with model version pinned.
16. **CI:** GitHub Actions running `opa test`, unit + Redis/OPA service-container integration tests.

---

*Continue with [05_backend_distsys_algos_stack.md](05_backend_distsys_algos_stack.md).*
