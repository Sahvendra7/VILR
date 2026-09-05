import re

with open('app/domain/gateway.py', 'r') as f:
    content = f.read()

imports = """
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
"""

content = content.replace('from app.execution.executor import PaymentExecutor', 'from app.execution.executor import PaymentExecutor\n' + imports)

investigate_method = """
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
"""

content = re.sub(r'    def __init__\(.*?\n        self\._tx_states: Dict\[str, StateController\] = \{\}', investigate_method, content, flags=re.DOTALL)

methods = """
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
            execution_result=record.execution_status or "NOT_REACHED",
            final_decision=record.authorization_status or "DENIED" if record.execution_status != "SUCCESS" else "AUTHORIZED",
            decision_source="SYSTEM",
            explanation_source="ExceptionIntelligence" if record.investigation else None,
            policy_version="1.0",
            audit_event_id=record.record_hash,
            previous_hash=record.prev_record_hash,
            current_hash=record.record_hash,
            timestamp=record.timestamp
        )
        return receipt
"""

content = content + methods

with open('app/domain/gateway.py', 'w') as f:
    f.write(content)
