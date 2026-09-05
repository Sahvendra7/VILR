import re

with open("app/domain/gateway.py", "r") as f:
    content = f.read()

# I will write a script to insert performance tracking and risk assessment
# To make it safer, I will do surgical replacements.

new_authorize = """    async def authorize(self, request: GatewayAuthorizeRequest) -> dict:
        perf = PerformanceTracker()
        
        tx_id = request.transaction_id
        state = StateController(TransactionState.INTENT_RECEIVED)
        self._tx_states[tx_id] = state
        
        context = {
            "user_id": request.user_intent.user_id,
            "merchant_id": request.cart.merchant_id,
        }
        
        risk_signals = []
        
        await self._log(tx_id, TransactionState.INTENT_RECEIVED, **context)
        
        try:
            perf.start("crypto_verification")
            open_mandate = await self.verifier.verify_open_checkout_mandate(
                request.open_checkout_token, request.user_public_key
            )
            state.transition_to(TransactionState.AP2_VERIFIED)
            await self._log(tx_id, TransactionState.AP2_VERIFIED, **context)
            
            closed_mandate = await self.verifier.verify_closed_checkout_mandate(
                request.closed_checkout_token, request.merchant_public_key
            )
            context["open_mandate_hash"] = closed_mandate.open_mandate_hash
            context["cart_hash"] = closed_mandate.cart_hash
            perf.stop("crypto_verification")
            
            perf.start("cart_verification")
            actual_cart_hash = compute_checkout_hash(request.cart)
            if actual_cart_hash != closed_mandate.cart_hash:
                raise HashMismatch("Cart hash does not match closed mandate")
                
            state.transition_to(TransactionState.CART_VERIFIED)
            await self._log(tx_id, TransactionState.CART_VERIFIED, **context)
            perf.stop("cart_verification")
            
        except (InvalidSignature, HashMismatch, MerchantUntrusted, MandateExpired) as e:
            if "crypto_verification" in perf._starts and "crypto_verification" not in perf.timings: perf.stop("crypto_verification")
            if "cart_verification" in perf._starts and "cart_verification" not in perf.timings: perf.stop("cart_verification")
            
            fail_state = TransactionState.INVALID_SIGNATURE
            if isinstance(e, HashMismatch):
                fail_state = TransactionState.HASH_MISMATCH
                risk_signals.append("CART_MISMATCH")
            if isinstance(e, MerchantUntrusted):
                fail_state = TransactionState.MERCHANT_UNTRUSTED
                risk_signals.append("MERCHANT_PROHIBITED")
            if isinstance(e, MandateExpired):
                fail_state = TransactionState.MANDATE_EXPIRED
                risk_signals.append("MANDATE_EXPIRED")
            if isinstance(e, InvalidSignature):
                risk_signals.append("SIGNATURE_FAILURE")
            
            state.transition_to(fail_state)
            context["failure_reason"] = str(e)
            
            risk = DeterministicRiskCalculator().calculate_risk(risk_signals)
            context["evidence"] = {"risk": risk.model_dump(mode='json')}
            
            await self._log(tx_id, fail_state, **context)
            raise

        perf.start("redis_latency")
        reservation_key = f"{closed_mandate.open_mandate_hash}:{closed_mandate.cart_hash}"
        reserved = await self.idempotency.try_reserve(reservation_key, tx_id, 300)
        perf.stop("redis_latency")
        
        if not reserved:
            state.transition_to(TransactionState.REPLAY_DETECTED)
            context["failure_reason"] = "Replay detected"
            risk_signals.append("REPLAY_DETECTED")
            risk = DeterministicRiskCalculator().calculate_risk(risk_signals)
            
            # Construct partial evidence for replay
            context["evidence"] = {
                "replay": {
                    "idempotency_key": str(reservation_key),
                    "replay_detected": True,
                    "reservation_status": "CONFLICT",
                    "execution_token_status": "NONE"
                },
                "risk": risk.model_dump(mode='json')
            }
            
            await self._log(tx_id, TransactionState.REPLAY_DETECTED, **context)
            raise ReplayDetected("Duplicate reservation")

        state.transition_to(TransactionState.RESERVATION_ACQUIRED)
        await self._log(tx_id, TransactionState.RESERVATION_ACQUIRED, **context)

        try:
            perf.start("gemini_latency")
            sem_result = await self.semantic.verify(request.user_intent, request.cart)
            perf.stop("gemini_latency")
            context["semantic_decision"] = sem_result.status
            context["semantic_confidence"] = sem_result.confidence
            
            if sem_result.status != "PASS":
                risk_signals.append("SEMANTIC_FAIL")
            
            state.transition_to(TransactionState.SEMANTIC_ANALYZED)
            await self._log(tx_id, TransactionState.SEMANTIC_ANALYZED, **context)
            
        except Exception as e:
            await self.idempotency.release(reservation_key, tx_id)
            raise

        try:
            perf.start("opa_latency")
            opa_input = {
                "mandate": open_mandate.constraints.model_dump(mode='json'),
                "cart": request.cart.model_dump(mode='json'),
                "semantic": {"status": sem_result.status, "confidence": sem_result.confidence},
                "current_time": int(datetime.now().timestamp())
            }
            decision = await self.policy.evaluate(opa_input)
            perf.stop("opa_latency")
            context["policy_decision"] = "ALLOW" if decision.allowed else "DENY"
            
            if not decision.allowed:
                risk_signals.append("POLICY_VIOLATION")
                
            risk = DeterministicRiskCalculator().calculate_risk(risk_signals)
            
            perf.start("evidence_construction")
            policy_meta = PolicyMetadata(name="payment_authorization", version=str(getattr(decision, "policy_version", "unknown")), hash=str(getattr(decision, "policy_hash", "unknown")))
            
            evidence = DecisionEvidence(
                intent=IntentEvidence(
                    intent_id=request.user_intent.user_id,
                    intent_timestamp=datetime.now(),
                    intent_status="VERIFIED",
                    intent_hash=str(open_mandate.intent_hash)
                ),
                cryptographic=CryptographicEvidence(
                    signature_verified=True,
                    intent_hash=str(open_mandate.intent_hash),
                    cart_hash=str(closed_mandate.cart_hash),
                    transaction_binding=True,
                    verification_result="SUCCESS"
                ),
                cart=CartEvidence(
                    expected_cart_hash=str(closed_mandate.cart_hash),
                    actual_cart_hash=str(actual_cart_hash),
                    cart_match=True,
                    expected_amount=str(request.cart.total_amount),
                    actual_amount=str(request.cart.total_amount)
                ),
                replay=ReplayEvidence(
                    idempotency_key=str(reservation_key),
                    replay_detected=False,
                    reservation_status="ACQUIRED",
                    execution_token_status="PENDING"
                ),
                semantic=SemanticEvidence(
                    semantic_result=str(sem_result.status),
                    confidence=float(sem_result.confidence),
                    detected_mismatches=[],
                    provider="GeminiLLMProvider",
                    advisory_only=True
                ) if sem_result else None,
                policy=PolicyEvidence(
                    policy_name=policy_meta.name,
                    policy_version=policy_meta.version,
                    policy_hash=policy_meta.hash,
                    policy_decision=str("ALLOW" if decision.allowed else "DENY"),
                    matched_rules=[],
                    violations=decision.violations
                ),
                execution=ExecutionEvidence(
                    execution_authorized=decision.allowed,
                    provider="Razorpay",
                    provider_request_id=None,
                    execution_status="NOT_REACHED"
                ),
                risk=risk
            )
            
            evidence_dict = evidence.model_dump(mode='json')
            canon_str = json.dumps(evidence_dict, separators=(',', ':'), sort_keys=True)
            evidence.evidence_hash = hashlib.sha256(canon_str.encode('utf-8')).hexdigest()
            evidence_dict["evidence_hash"] = evidence.evidence_hash
            perf.stop("evidence_construction")
            
            perf.start("policy_explanation")
            explainer = DeterministicPolicyExplainer(policy_meta)
            explanation = explainer.explain(decision, opa_input)
            perf.stop("policy_explanation")
            
            context["evidence"] = evidence_dict
            context["explanation"] = explanation.model_dump(mode='json')
            context["policy_version"] = policy_meta.version
            
            if not decision.allowed:
                state.transition_to(TransactionState.POLICY_DENIED)
                await self._log(tx_id, TransactionState.POLICY_DENIED, **context)
                raise PolicyViolation("Transaction denied by policy")
                
            state.transition_to(TransactionState.AUTHORIZED)
            context["authorization_status"] = "AUTHORIZED"
            
            perf.start("audit_latency")
            await self._log(tx_id, TransactionState.AUTHORIZED, **context)
            perf.stop("audit_latency")
            
            perf.stop_all()
            # Store timings for benchmark output if needed
            self._last_perf = perf.timings
            
            import secrets
            execution_token = secrets.token_urlsafe(32)
            await self.idempotency.issue_execution_token(
                execution_token, tx_id,
                str(request.cart.total_amount), request.cart.currency,
                request.cart.merchant_id, closed_mandate.open_mandate_hash
            )
            
            state.transition_to(TransactionState.RESERVATION_COMMITTED)
            await self._log(tx_id, TransactionState.RESERVATION_COMMITTED, **context)
            
            return {
                "transaction_id": tx_id,
                "status": "AUTHORIZED",
                "execution_token": execution_token,
                "reservation_status": "COMMITTED"
            }

        except Exception as e:
            if not isinstance(e, (PolicyViolation, ReplayDetected)):
                await self.idempotency.release(reservation_key, tx_id)
            raise"""

content = re.sub(r'    async def authorize\(self, request: GatewayAuthorizeRequest\) -> dict:.*?        except Exception as e:\n            if not isinstance\(e, \(PolicyViolation, ReplayDetected\)\):\n                await self.idempotency.release\(reservation_key, tx_id\)\n            raise', new_authorize, content, flags=re.DOTALL)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)

