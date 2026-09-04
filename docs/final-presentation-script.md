# Final Presentation Script

## 10-Second Opening
"AI agents are ready to negotiate and shop on our behalf, but we cannot safely give them raw API keys. VILR is a zero-trust gateway that uses cryptography and deterministic policies to authorize agent-driven payments safely."

## 30-Second Pitch
"Agentic commerce today relies on giving bots unrestricted API access, leading to hallucination-driven risk. VILR sits in the critical path between the merchant and the payment gateway. It cryptographically binds a user's natural language intent to the checkout cart, applies AI to evaluate semantics probabilistically, but relies strictly on deterministic OPA policies and Redis locking to authorize financial execution. The AI negotiates, but the cryptography executes."

## 2-Minute Technical Explanation
"If we look at an unprotected agent, a single prompt injection can drain a user's wallet. If we add basic rules, agents still get tricked by manipulated carts. VILR fixes this via a multi-layered trust boundary. 

First, we use RFC 8785 JSON canonicalization to ensure the cart hasn't been tampered with. Second, we isolate the LLM—it only provides probabilistic *evidence* about whether a 'gaming rig' matches the intent of a 'laptop'. Third, an Open Policy Agent strictly enforces the financial rules: even if the AI is tricked into giving a 99% PASS, if the cart is $1 over budget, OPA kills it. Finally, Redis ensures the transaction fires safely authorized and protected against concurrency at the gateway level. It’s a zero-trust architecture tailored specifically for the age of autonomous agentic payments, ensuring unauthorized payment execution remains at 0%."

## 5-Minute Complete Presentation

**0:00 - 0:30 (The Problem)**
"Hello. Today, we're building the future of agentic commerce. But there's a massive gap: AI agents hallucinate. They get confused by prompt injections. We cannot safely hand them raw API keys to move money. If an agent buys a $9,000 gaming rig instead of a $500 laptop, the liability is undefined."

**0:30 - 1:00 (The Solution)**
"Meet VILR. VILR separates *intent understanding* from *financial execution*. We place a zero-trust gateway between the agent's checkout cart and the payment provider. We don't trust the agent, and we don't trust the merchant."

**1:00 - 1:30 (Architecture Boundaries)**
"We built four distinct boundaries:
1. **Crypto Layer:** Verifies the user's intent is cryptographically bound to the cart using JCS canonicalization and ECDSA P-256 signatures.
2. **Semantic Layer:** Probabilistically checks if the cart matches the natural language intent.
3. **OPA Layer:** Deterministically blocks transactions that exceed budgets or hit untrusted merchants.
4. **Redis Layer:** Guarantees atomic, at-most-once gateway authorization."

**1:30 - 3:00 (Live Demo - See 90-Second Hero Demo Below)**
*[Execute Demo]*

**3:00 - 3:45 (Resilience: Concurrency & State)**
"What happens under load? If a buggy agent fires 100 checkout requests simultaneously, our Redis Lua scripts enforce a two-phase reservation lock. Exactly 1 execution token is minted. 99 requests are rejected. And if the payment provider times out? We transition to `PAYMENT_UNKNOWN` and safely hold the state without retrying, ensuring no double-charges."

**3:45 - 4:30 (Security & Benchmark Results)**
"We benchmarked VILR against 186 adversarial attacks: Prompt injections, cart tampering, replays, and concurrent executions.
Result? 180 attacks Blocked, 6 Detected safely. 0 unauthorized payments executed. Our deterministic gateway evaluates these protections in under 10 milliseconds."

**4:30 - 5:00 (Razorpay Fit & Conclusion)**
"VILR is the missing piece for Razorpay's Agent Studio. It provides the safest infrastructure in the world to process AI-driven commerce. Thank you."

---

## 90-Second Hero Demo Script
*(Command: `python -m scripts.cli hero`)*

**Narrator:** "Let's watch VILR protect a user. The user asks their agent: 'Buy me a Dell or Lenovo laptop for coding under ₹50,000'."
**Screen:** Shows the intent received.
**Narrator:** "The agent visits a merchant. The merchant has embedded malicious metadata in the page. The agent gets confused and proposes a $9,000 gaming rig."
**Screen:** Shows the Semantic Verification layer processing the cart.
**Narrator:** "VILR intercepts the checkout. The LLM flags a semantic mismatch. But even if the LLM was tricked..."
**Screen:** Shows OPA returning DENY (BUDGET_EXCEEDED).
**Narrator:** "OPA deterministically denies the transaction because it exceeds the ₹50,000 budget. Zero payment provider calls are made."
**Screen:** Shows Audit Ledger recording the blocked attack.
**Narrator:** "The execution is rejected, the user's money is safe, and the entire attempt is recorded in an tamper-evident hash chain for cryptographic evidence."

---

## 10 Hardest Judge Questions and Answers

**Q1: What if the AI hallucinates a PASS on a fraudulent transaction?**
- **1-Sentence:** OPA still strictly enforces the budget and allowed merchant list.
- **Deep:** The semantic assessment is merely untrusted evidence fed into OPA. If the AI returns 99% confidence for a $500 cart on a $100 budget limit, OPA statically denies it (`allow == false`). VILR's architecture treats AI as probabilistic and OPA as deterministic.

**Q2: Why not just use OAuth?**
- **1-Sentence:** OAuth authorizes *who* the agent is, not *what* the transaction is.
- **Deep:** OAuth delegates scopes (e.g., `payment:write`). Once an agent has the token, it can execute *any* payment. VILR authorizes the specific payload cryptographically tied to the user's granular intent.

**Q3: How do you prevent replay attacks under high concurrency?**
- **1-Sentence:** Using a composite Redis key (`open_mandate_hash:checkout_hash`) and an atomic execution token.
- **Deep:** Before authorization, we `SETNX` a reservation key in Redis. If 100 identical requests hit the gateway, only one gets the reservation via Lua scripts. The winner gets a single-use execution token.

**Q4: What if Redis goes down?**
- **1-Sentence:** VILR fails closed; no reservation means no payment.
- **Deep:** If Redis is unavailable, the `try_reserve` phase throws a ConnectionError which the Gateway translates into an HTTP 503. The payment is safely rejected without side-effects.

**Q5: Doesn't Cryptography guarantee the payment is correct?**
- **1-Sentence:** Cryptography guarantees the cart hasn't been tampered with since checkout, but it doesn't guarantee the AI picked the right items.
- **Deep:** JCS and ECDSA P-256 prove that the merchant didn't manipulate prices *after* the agent created the cart. They do not execute the payment or validate semantic intent.

**Q6: Does VILR guarantee exactly-once payment execution?**
- **1-Sentence:** VILR guarantees at-most-once *gateway authorization*, relying on the payment provider's idempotency keys for exactly-once execution.
- **Deep:** Our Redis execution token prevents duplicate gateway processing. However, exactly-once external payment requires Razorpay's native provider-side idempotency handling.

**Q7: What happens if Razorpay times out during a payment call?**
- **1-Sentence:** The system transitions to a `PAYMENT_UNKNOWN` state without retrying.
- **Deep:** To prevent double-charging, VILR never automatically retries an unknown state. The execution token is marked consumed, and the transaction awaits an asynchronous worker to reconcile the true state.

**Q8: Does VILR automatically transfer legal liability?**
- **1-Sentence:** No, it provides cryptographically verifiable audit trails for dispute resolution, not automatic legal transfer.
- **Deep:** The SHA-256 hash chain provides indisputable cryptographic evidence of what intent was authorized and what was executed, which heavily assists in arbitrating disputes, but legal liability depends on external user agreements.

**Q9: Why not eliminate the LLM and use a deterministic ontology?**
- **1-Sentence:** Deterministic ontologies fail at scale because merchants don't standardize their descriptions.
- **Deep:** Hardcoding "Laptop" fails if the merchant lists "Dell XPS 13 9310". We need probabilistic AI to bridge unstructured merchant data with user intent, but we sandbox that AI behind deterministic rules.

**Q10: What limits VILR from being production-ready today?**
- **1-Sentence:** It requires transitioning to a production HSM for keys and a distributed ledger for the audit chain.
- **Deep:** We used a local signer and SQLite for hackathon velocity. Production requires AWS KMS/HashiCorp Vault for key management and a highly available distributed database (like Amazon QLDB) for the tamper-evident ledger.
