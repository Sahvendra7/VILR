from decimal import Decimal
from app.security.crypto import compute_checkout_hash
import uuid
import secrets
from typing import Dict, Any, Optional
from datetime import datetime

import time
from app.domain.performance import PerformanceTracker
from app.security.risk import DeterministicRiskCalculator

from app.domain.models import (
    DecisionEvidence, IntentEvidence, CryptographicEvidence, CartEvidence,
    ReplayEvidence, SemanticEvidence, PolicyEvidence, ExecutionEvidence, PolicyMetadata
)
from app.policy.explainability import DeterministicPolicyExplainer
from datetime import datetime

import time
from app.domain.performance import PerformanceTracker
from app.security.risk import DeterministicRiskCalculator

import hashlib
import json

from pydantic import BaseModel
from structlog import get_logger

from app.domain.models import (
    ExecutionRequest, ExecutionReceipt,
    UserIntent, Cart, AuditRecord
)
from app.domain.state_machine import StateController, TransactionState
from app.domain.errors import (
    PolicyDenied,
    InvalidStateTransition, MandateExpired, InvalidSignature, HashMismatch,
    MerchantUntrusted, ReplayDetected, SemanticDrift, PolicyDenied,
    PaymentUnknown, DuplicateExecution, InvalidRequest, VILRError, IdempotencyConflict
)
from app.domain.interfaces import (
    MandateVerifier, IdempotencyStore, SemanticVerifier,
    PolicyEngine, AuditLedger
)
from app.execution.executor import PaymentExecutor

from app.exception.intelligence import (
    ExceptionIntelligenceLayer, 
    InvestigationContext, 
    ExceptionCategory, 
    Severity, 
    RecommendedAction, 
    DecisionSource,
    ExceptionInvestigation
)
from app.domain.models import SecurityReceipt


logger = get_logger(__name__)

class GatewayAuthorizeRequest(BaseModel):
    transaction_id: str
    open_checkout_token: str
    closed_checkout_token: str
    user_intent: UserIntent
    cart: Cart
    user_public_key: dict
    merchant_public_key: dict

class GatewayExecuteRequest(BaseModel):
    transaction_id: str
    execution_token: str
    amount: Decimal
    currency: str
    merchant_id: str
    mandate_hash: str
    provider_idempotency_key: str
    payment_method_id: str

class GatewayOrchestrator:

    def __init__(
        self,
        verifier: MandateVerifier,
        idempotency: IdempotencyStore,
        semantic: SemanticVerifier,
        policy: PolicyEngine,
        payment_executor: PaymentExecutor,
        audit: AuditLedger,
        exception_intelligence: Optional[ExceptionIntelligenceLayer] = None
    ):
        self.verifier = verifier
        self.idempotency = idempotency
        self.semantic = semantic
        self.policy = policy
        self.payment_executor = payment_executor
        self.audit = audit
        self.exception_intelligence = exception_intelligence
        
        self._tx_states: Dict[str, StateController] = {}


    async def _log(self, tx_id, state, **kwargs):
        logger.info(state.value, transaction_id=tx_id, **kwargs)
        last = await self.audit.get(tx_id)
        from app.audit.ledger import GENESIS_HASH
        prev_hash = last.record_hash if last else GENESIS_HASH
        
        data = {
            "transaction_id": tx_id,
            "user_id": kwargs.get("user_id", "unknown"),
            "agent_id": kwargs.get("agent_id", "unknown"),
            "merchant_id": kwargs.get("merchant_id", "unknown"),
            "intent_hash": kwargs.get("intent_hash", "unknown"),
            "open_mandate_hash": kwargs.get("open_mandate_hash", "unknown"),
            "cart_hash": kwargs.get("cart_hash", "unknown"),
            "policy_decision": kwargs.get("policy_decision"),
            "semantic_decision": kwargs.get("semantic_decision"),
            "semantic_confidence": kwargs.get("semantic_confidence"),
            "authorization_status": kwargs.get("authorization_status"),
            "timestamp": datetime.now(),
            "nonce": uuid.uuid4().hex,
            "payment_attempt_id": kwargs.get("payment_attempt_id"),
            "execution_status": kwargs.get("execution_status"),
            "failure_reason": kwargs.get("failure_reason"),
            "state": state.value,
            "prev_record_hash": prev_hash,
            "investigation": kwargs.get("investigation"),
            "evidence": kwargs.get("evidence"),
            "explanation": kwargs.get("explanation")
        }
        
        if hasattr(self.audit, "build_record"):
            rec = self.audit.build_record(data)
        else:
            rec = AuditRecord(**data)
        await self.audit.record(rec)

    async def authorize(self, request: GatewayAuthorizeRequest) -> dict:
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
            state.transition_to(TransactionState.POLICY_EVALUATED)
            await self._log(tx_id, TransactionState.POLICY_EVALUATED, **context)
            
            if not decision.allowed:
                risk_signals.append("POLICY_VIOLATION")
                
            perf.start("risk_latency")
            risk = DeterministicRiskCalculator().calculate_risk(risk_signals)
            perf.stop("risk_latency")
            
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
                raise PolicyDenied("Transaction denied by policy")
                
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
            if not isinstance(e, (PolicyDenied, ReplayDetected)):
                await self.idempotency.release(reservation_key, tx_id)
            raise

    async def execute(self, request: GatewayExecuteRequest) -> dict:
        tx_id = request.transaction_id
        
        try:
            auth_data = await self.idempotency.consume_execution_token(
                request.execution_token, tx_id, 
                str(request.amount), request.currency, request.merchant_id, request.mandate_hash
            )
        except DuplicateExecution as e:
            # Token already consumed -> execution replay
            state = self._tx_states.get(tx_id)
            if state:
                state.transition_to(TransactionState.REPLAY_DETECTED)
                context_replay = {
                    "merchant_id": request.merchant_id,
                    "payment_attempt_id": request.provider_idempotency_key,
                    "failure_reason": "Execution token already consumed",
                    "evidence": {
                        "replay": {
                            "idempotency_key": request.execution_token,
                            "replay_detected": True,
                            "reservation_status": "COMMITTED",
                            "execution_token_status": "ALREADY_CONSUMED"
                        }
                    }
                }
                await self._log(tx_id, TransactionState.REPLAY_DETECTED, **context_replay)
            raise
        except ValueError as e:
            raise InvalidRequest(str(e))

        state = self._tx_states.get(tx_id)
        if not state:
            raise InvalidStateTransition("State not found")

        exec_request = ExecutionRequest(
            transaction_id=tx_id,
            idempotency_key=request.provider_idempotency_key,
            merchant_id=request.merchant_id,
            amount=request.amount,
            currency=request.currency,
            payment_method_id=request.payment_method_id,
            mandate_hash=request.mandate_hash
        )

        context = {
            "merchant_id": request.merchant_id,
            "open_mandate_hash": request.mandate_hash,
            "payment_attempt_id": request.provider_idempotency_key
        }

        try:
            receipt = await self.payment_executor.execute(exec_request, state)
            context["execution_status"] = receipt.status
            
            # Retrieve prior record to update evidence
            prior_record = await self.audit.get(tx_id)
            if prior_record and prior_record.evidence:
                ev = prior_record.evidence.copy()
                if "execution" in ev:
                    ev["execution"]["execution_status"] = receipt.status
                    ev["execution"]["provider_request_id"] = receipt.provider_transaction_id or request.provider_idempotency_key
                context["evidence"] = ev
                
            await self._log(tx_id, state.current_state, **context)
            
            return {
                "transaction_id": tx_id,
                "payment_id": receipt.provider_transaction_id,
                "status": receipt.status,
                "timestamp": receipt.timestamp.isoformat(),
                "provider_idempotency_key": request.provider_idempotency_key
            }
        except Exception as e:
            context["failure_reason"] = str(e)
            context["execution_status"] = "FAILED"
            await self._log(tx_id, state.current_state, **context)
            raise

    async def resolve_unknown(self, transaction_id: str, provider_idempotency_key: str) -> dict:
        state = self._tx_states.get(transaction_id)
        if not state:
            raise InvalidRequest("Transaction state not found")

        receipt = await self.payment_executor.reconcile(provider_idempotency_key, state)
        if not receipt:
            raise PaymentUnknown("Provider returned no status for this key")

        context = {
            "payment_attempt_id": provider_idempotency_key,
            "execution_status": receipt.status
        }
        await self._log(transaction_id, state.current_state, **context)

        return {
            "transaction_id": transaction_id,
            "payment_id": receipt.provider_transaction_id,
            "status": receipt.status,
            "timestamp": receipt.timestamp.isoformat(),
            "provider_idempotency_key": provider_idempotency_key
        }

    async def investigate_transaction(self, transaction_id: str) -> ExceptionInvestigation:
        if not self.exception_intelligence:
            raise ValueError("Exception intelligence not configured")
            
        record = await self.audit.get(transaction_id)
        if not record:
            raise ValueError("No audit record found for transaction")
            
        if record.execution_status == "SUCCESS":
            raise ValueError("Cannot investigate successful transaction")

        context = InvestigationContext(
            request_id=transaction_id,
            intent_id=record.intent_hash,
            transaction_id=transaction_id,
            workflow_state=record.state,
            deterministic_decision=record.authorization_status or record.execution_status or "DENIED",
            failure_code=record.failure_reason,
            relevant_evidence=[f"State: {record.state}", f"Reason: {record.failure_reason}"],
            policy_result={"decision": record.policy_decision},
            semantic_result={"decision": record.semantic_decision, "confidence": record.semantic_confidence},
            provider_result={"status": record.execution_status}
        )
        
        investigation = await self.exception_intelligence.investigate(context)
        
        # Log investigation to audit
        investigation_data = investigation.model_dump(mode='json')
        await self._log(transaction_id, StateController(TransactionState(record.state)).current_state, investigation=investigation_data)
        
        return investigation

    async def generate_receipt(self, transaction_id: str) -> SecurityReceipt:
        record = await self.audit.get(transaction_id)
        if not record:
            raise ValueError("Transaction not found in audit")
            
        execution_status = record.execution_status or "NOT_REACHED"
        if record.state == "REPLAY_DETECTED":
            execution_status = "BLOCKED_REPLAY"
            
        provider_call = "NO" if execution_status in ["NOT_REACHED", "BLOCKED_REPLAY"] else "YES"
        
        provider_request_id = record.payment_attempt_id if hasattr(record, "payment_attempt_id") and record.payment_attempt_id else None
        
        automatic_retry = "NO" if execution_status == "UNKNOWN" else None
        reconciliation = "REQUIRED" if execution_status == "UNKNOWN" else None

        receipt = SecurityReceipt(
            receipt_id=f"rec_{transaction_id}",
            request_id=transaction_id,
            intent_id=record.intent_hash,
            transaction_id=transaction_id,
            intent_verified=record.intent_hash != "unknown",
            cryptographic_verification=record.cart_hash != "unknown",
            cart_verified=record.cart_hash != "unknown",
            replay_check="CLEAR" if record.state not in ["REPLAY_DETECTED"] else "FAILED",
            semantic_result=record.semantic_decision,
            policy_result=record.policy_decision or "NOT_REACHED",
            execution_result=execution_status,
            execution_status=execution_status,
            provider_call=provider_call,
            provider_request_id=provider_request_id,
            automatic_retry=automatic_retry,
            reconciliation=reconciliation,
            final_decision=record.authorization_status or ("DENIED" if record.execution_status != "SUCCESS" else "AUTHORIZED"),
            decision_source="SYSTEM",
            explanation_source="ExceptionIntelligence" if record.investigation else None,
            policy_version=record.explanation.get("policy_version", "1.0") if getattr(record, "explanation", None) else "1.0",
            evidence=record.evidence,
            explanation=record.explanation,
            risk=record.evidence.get("risk") if record.evidence else None,
            audit_event_id=record.record_hash,
            previous_hash=record.prev_record_hash,
            current_hash=record.record_hash,
            timestamp=record.timestamp
        )
        return receipt
