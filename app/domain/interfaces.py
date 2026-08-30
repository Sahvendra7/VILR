from typing import Protocol, Tuple, Optional, List
from app.domain.models import (
    UserIntent, Cart, SemanticAssessment, AuthorizationDecision,
    ExecutionRequest, ExecutionReceipt, AuditRecord,
    OpenCheckoutMandate, OpenPaymentMandate,
    ClosedCheckoutMandate, ClosedPaymentMandate
)

class MandateVerifier(Protocol):
    async def verify_open_checkout_mandate(self, token: str, user_public_key: dict) -> OpenCheckoutMandate:
        ...
    
    async def verify_closed_checkout_mandate(self, token: str, merchant_public_key: dict) -> ClosedCheckoutMandate:
        ...

class IdempotencyStore(Protocol):
    async def try_reserve(self, key: str, transaction_id: str, ttl_seconds: int) -> bool:
        ...
        
    async def commit(self, key: str) -> None:
        ...
        
    async def release(self, key: str, transaction_id: str) -> None:
        ...
        
    async def is_reserved_or_committed(self, key: str) -> Tuple[bool, Optional[str]]:
        ...

class LLMProvider(Protocol):
    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> dict:
        ...

class SemanticVerifier(Protocol):
    async def verify(self, intent: UserIntent, cart: Cart) -> SemanticAssessment:
        ...

class PolicyEngine(Protocol):
    async def evaluate(self, input_data: dict) -> AuthorizationDecision:
        ...

class PaymentProvider(Protocol):
    async def execute_payment(self, request: ExecutionRequest) -> ExecutionReceipt:
        ...

class AuditLedger(Protocol):
    async def record(self, record: AuditRecord) -> None:
        ...
        
    async def get(self, transaction_id: str) -> Optional[AuditRecord]:
        ...
        
    async def list_by_user(self, user_id: str) -> List[AuditRecord]:
        ...
        
    async def verify_chain(self) -> Tuple[bool, Optional[int]]:
        ...
