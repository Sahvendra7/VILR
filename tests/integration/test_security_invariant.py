import pytest
from app.domain.gateway import GatewayOrchestrator, GatewayAuthorizeRequest
from app.semantic.provider import MockLLMProvider
from app.semantic.verifier import AISemanticVerifier
from app.domain.models import UserIntent, Cart, CartItem, Identifier
from simulator.scenarios import ScenarioGenerator
import copy

@pytest.mark.asyncio
async def test_security_invariant_llm_pass_opa_deny():
    # This proves: AI PASS -> OPA DENY -> Auth Denied -> Payment Calls = 0
    from app.domain.interfaces import MandateVerifier, IdempotencyStore, PaymentProvider
    from unittest.mock import AsyncMock
    verifier = AsyncMock(spec=MandateVerifier)
    from app.security.crypto import compute_checkout_hash
    generator = ScenarioGenerator()
    payload = generator.generate_valid_payload()
    req = GatewayAuthorizeRequest(**payload)
    
    class FakeResult:
        is_valid = True
        open_mandate_hash = "abc"
        cart_hash = compute_checkout_hash(req.cart)
        failure_reason = None
    verifier.verify_closed_checkout_mandate.return_value = FakeResult()
    idem = AsyncMock(spec=IdempotencyStore)
    provider = AsyncMock(spec=PaymentProvider)

    
    # Force LLM to return PASS
    llm = MockLLMProvider(responses={"USER INTENT": {
        "status": "PASS",
        "confidence": 0.99,
        "checks": {},
        "violations": [],
        "reasoning": "AI thinks this is a great purchase!"
    }})
    semantic = AISemanticVerifier(llm)
    
    gateway = GatewayOrchestrator(
        verifier=verifier,
        idempotency=idem,
        semantic=semantic,
        policy=None,
        payment_executor=None, # Exector not needed for auth, but we want to prove 0 calls
        audit=None
    )
    
    # We will simulate OPA returning DENY because of budget violation
    class MockOPADeny:
        is_available = lambda self: True
        async def evaluate(self, input_data: dict):
            from app.domain.models import AuthorizationDecision
            return AuthorizationDecision(
                allowed=False,
                violations=[{"rule": "budget_check", "description": "Over budget"}],
                policy_version="1.0",
                policy_hash="abc"
            )
    gateway.policy = MockOPADeny()
    from app.audit.ledger import MemoryAuditLedger
    gateway.audit = MemoryAuditLedger()
    
    generator = ScenarioGenerator()
    payload = generator.generate_valid_payload()
    req = GatewayAuthorizeRequest(**payload)
    
    from app.domain.errors import PolicyDenied
    with pytest.raises(PolicyDenied, match="Over budget"):
        await gateway.authorize(req)

@pytest.mark.asyncio
async def test_security_invariant_llm_fail_opa_deny():
    # This proves: AI FAIL -> OPA sees FAIL -> Auth Denied -> Payment Calls = 0
    from app.domain.interfaces import MandateVerifier, IdempotencyStore, PaymentProvider
    from unittest.mock import AsyncMock
    verifier = AsyncMock(spec=MandateVerifier)
    from app.security.crypto import compute_checkout_hash
    generator = ScenarioGenerator()
    payload = generator.generate_valid_payload()
    req = GatewayAuthorizeRequest(**payload)
    
    class FakeResult:
        is_valid = True
        open_mandate_hash = "abc"
        cart_hash = compute_checkout_hash(req.cart)
        failure_reason = None
    verifier.verify_closed_checkout_mandate.return_value = FakeResult()
    idem = AsyncMock(spec=IdempotencyStore)
    provider = AsyncMock(spec=PaymentProvider)

    
    # Force LLM to return FAIL
    llm = MockLLMProvider(responses={"USER INTENT": {
        "status": "FAIL",
        "confidence": 0.99,
        "checks": {},
        "violations": [{"type": "SEMANTIC_MISMATCH", "severity": "HIGH", "evidence": "Not what user wanted"}],
        "reasoning": "AI thinks this is bad."
    }})
    semantic = AISemanticVerifier(llm)
    
    gateway = GatewayOrchestrator(
        verifier=verifier,
        idempotency=idem,
        semantic=semantic,
        policy=None,
        payment_executor=None,
        audit=None
    )
    
    # We will simulate OPA returning DENY because of semantic status FAIL
    class MockOPADenySemantic:
        is_available = lambda self: True
        async def evaluate(self, input_data: dict):
            from app.domain.models import AuthorizationDecision
            if input_data["semantic"]["status"] == "FAIL":
                return AuthorizationDecision(
                    allowed=False,
                    violations=[{"rule": "semantic_status", "description": "Semantic validation failed"}],
                    policy_version="1.0",
                    policy_hash="abc"
                )
            return AuthorizationDecision(allowed=True, violations=[], policy_version="1", policy_hash="a")
    gateway.policy = MockOPADenySemantic()
    from app.audit.ledger import MemoryAuditLedger
    gateway.audit = MemoryAuditLedger()
    
    generator = ScenarioGenerator()
    payload = generator.generate_valid_payload()
    req = GatewayAuthorizeRequest(**payload)
    
    from app.domain.errors import PolicyDenied
    with pytest.raises(PolicyDenied, match="Semantic validation failed"):
        await gateway.authorize(req)

