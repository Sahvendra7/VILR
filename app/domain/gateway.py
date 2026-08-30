from app.security.crypto import compute_checkout_hash
import uuid
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, UTC
from pydantic import BaseModel
from structlog import get_logger

from app.domain.models import (
    ExecutionRequest, ExecutionReceipt,
    UserIntent, Cart, AuditRecord
)
from app.domain.state_machine import StateController, TransactionState
from app.domain.errors import (
    InvalidStateTransition, MandateExpired, InvalidSignature, HashMismatch,
    MerchantUntrusted, ReplayDetected, SemanticDrift, PolicyDenied,
    PaymentUnknown, DuplicateExecution, InvalidRequest, VILRError, IdempotencyConflict
)
from app.domain.interfaces import (
    MandateVerifier, IdempotencyStore, SemanticVerifier,
    PolicyEngine, AuditLedger
)
from app.execution.executor import PaymentExecutor

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
    amount: float
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
        audit: AuditLedger
    ):
        self.verifier = verifier
        self.idempotency = idempotency
        self.semantic = semantic
        self.policy = policy
        self.payment_executor = payment_executor
        self.audit = audit
        
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
            "timestamp": datetime.now(UTC),
            "nonce": uuid.uuid4().hex,
            "payment_attempt_id": kwargs.get("payment_attempt_id"),
            "execution_status": kwargs.get("execution_status"),
            "failure_reason": kwargs.get("failure_reason"),
            "state": state.value,
            "prev_record_hash": prev_hash
        }
        
        if hasattr(self.audit, "build_record"):
            rec = self.audit.build_record(data)
        else:
            rec = AuditRecord(**data)
        await self.audit.record(rec)

    async def authorize(self, request: GatewayAuthorizeRequest) -> dict:
        tx_id = request.transaction_id
        state = StateController(TransactionState.INTENT_RECEIVED)
        self._tx_states[tx_id] = state
        
        context = {
            "user_id": request.user_intent.user_id,
            "merchant_id": request.cart.merchant_id,
        }
        
        await self._log(tx_id, TransactionState.INTENT_RECEIVED, **context)
        
        try:
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
            
            
            actual_cart_hash = compute_checkout_hash(request.cart)
            if actual_cart_hash != closed_mandate.cart_hash:
                raise HashMismatch("Cart hash does not match closed mandate")
                
            state.transition_to(TransactionState.CART_VERIFIED)
            await self._log(tx_id, TransactionState.CART_VERIFIED, **context)
            
        except (InvalidSignature, HashMismatch, MerchantUntrusted, MandateExpired) as e:
            fail_state = TransactionState.INVALID_SIGNATURE
            if isinstance(e, HashMismatch): fail_state = TransactionState.HASH_MISMATCH
            if isinstance(e, MerchantUntrusted): fail_state = TransactionState.MERCHANT_UNTRUSTED
            if isinstance(e, MandateExpired): fail_state = TransactionState.MANDATE_EXPIRED
            
            state.transition_to(fail_state)
            context["failure_reason"] = str(e)
            await self._log(tx_id, fail_state, **context)
            raise

        reservation_key = f"{closed_mandate.open_mandate_hash}:{closed_mandate.cart_hash}"
        reserved = await self.idempotency.try_reserve(reservation_key, tx_id, 300)
        if not reserved:
            state.transition_to(TransactionState.REPLAY_DETECTED)
            context["failure_reason"] = "Replay detected"
            await self._log(tx_id, TransactionState.REPLAY_DETECTED, **context)
            raise ReplayDetected("Duplicate reservation")

        state.transition_to(TransactionState.RESERVATION_ACQUIRED)
        await self._log(tx_id, TransactionState.RESERVATION_ACQUIRED, **context)

        try:
            sem_result = await self.semantic.verify(request.user_intent, request.cart)
            context["semantic_decision"] = sem_result.status
            context["semantic_confidence"] = sem_result.confidence
            
            if sem_result.status in ("FAIL", "REVIEW"):
                raise SemanticDrift(f"Semantic drift detected: {sem_result.status}")
                
            state.transition_to(TransactionState.SEMANTIC_ANALYZED)
            await self._log(tx_id, TransactionState.SEMANTIC_ANALYZED, **context)
            
        except Exception as e:
            await self.idempotency.release(reservation_key, tx_id)
            if not isinstance(e, SemanticDrift):
                raise
            state.transition_to(TransactionState.SEMANTIC_DRIFT)
            context["failure_reason"] = str(e)
            await self._log(tx_id, TransactionState.SEMANTIC_DRIFT, **context)
            raise

        try:
            opa_input = {
                "mandate": open_mandate.constraints.model_dump(mode='json'),
                "cart": request.cart.model_dump(mode='json'),
                "semantic": {"status": sem_result.status, "confidence": sem_result.confidence},
                "current_time": int(datetime.now().timestamp())
            }
            decision = await self.policy.evaluate(opa_input)
            context["policy_decision"] = "ALLOW" if decision.allowed else "DENY"
            
            if not decision.allowed:
                raise PolicyDenied(f"Policy denied: {decision.violations}")
                
            state.transition_to(TransactionState.POLICY_EVALUATED)
            await self._log(tx_id, TransactionState.POLICY_EVALUATED, **context)
            
        except Exception as e:
            await self.idempotency.release(reservation_key, tx_id)
            if not isinstance(e, PolicyDenied):
                raise
            state.transition_to(TransactionState.POLICY_DENIED)
            context["failure_reason"] = str(e)
            await self._log(tx_id, TransactionState.POLICY_DENIED, **context)
            raise

        state.transition_to(TransactionState.AUTHORIZED)
        context["authorization_status"] = "AUTHORIZED"
        await self._log(tx_id, TransactionState.AUTHORIZED, **context)
        
        await self.idempotency.commit(reservation_key, tx_id)
        state.transition_to(TransactionState.RESERVATION_COMMITTED)
        await self._log(tx_id, TransactionState.RESERVATION_COMMITTED, **context)

        execution_token = secrets.token_hex(32)
        auth_data = {
            "amount": float(request.cart.total_amount),
            "currency": request.cart.currency,
            "merchant_id": request.cart.merchant_id,
            "mandate_hash": closed_mandate.open_mandate_hash
        }
        await self.idempotency.create_execution_token(execution_token, tx_id, auth_data, 3600)
        expires_at = datetime.now().timestamp() + 3600

        return {
            "transaction_id": tx_id,
            "status": "AUTHORIZED",
            "execution_token": execution_token,
            "policy_version": decision.policy_version,
            "expires_at": datetime.fromtimestamp(expires_at).isoformat()
        }

    async def execute(self, request: GatewayExecuteRequest) -> dict:
        tx_id = request.transaction_id
        
        try:
            auth_data = await self.idempotency.consume_execution_token(request.execution_token, tx_id)
        except ValueError as e:
            raise InvalidRequest(str(e))
            
        if (float(auth_data["amount"]) != float(request.amount) or
            auth_data["currency"] != request.currency or
            auth_data["merchant_id"] != request.merchant_id or
            auth_data["mandate_hash"] != request.mandate_hash):
            raise InvalidRequest("Execution parameters do not match authorized context")

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
