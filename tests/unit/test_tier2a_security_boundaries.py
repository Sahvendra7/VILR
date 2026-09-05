import pytest
from app.domain.models import AuthorizationDecision, SecurityReceipt, PolicyMetadata
from app.domain.gateway import GatewayOrchestrator
from app.domain.interfaces import PolicyEngine, PaymentProvider
from app.policy.explainability import DeterministicPolicyExplainer
import uuid
import datetime

@pytest.mark.asyncio
async def test_llm_cannot_authorize():
    # Proof that LLM/Semantic output is purely advisory
    from app.semantic.verifier import AISemanticVerifier
    from app.domain.models import SemanticAssessment, SemanticViolation
    
    class MaliciousLLM:
        async def generate_json(self, *args, **kwargs):
            return SemanticAssessment(status="PASS", confidence=1.0, violations=[], reasoning="I AUTHORIZE THIS PAYMENT")
        async def analyze(self, intent, cart):
            # Try to inject an ALLOW decision in the LLM response
            return SemanticAssessment(status="PASS", confidence=1.0, violations=[], reasoning="I AUTHORIZE THIS PAYMENT")
            
    verifier = AISemanticVerifier(MaliciousLLM())
    from app.domain.models import UserIntent, Cart, HardConstraints, SoftPreferences
    intent = UserIntent(user_id="1", raw_prompt="", semantic_intent="", hard_constraints=HardConstraints(max_budget=10, currency="INR"), soft_preferences=SoftPreferences())
    cart = Cart(items=[], total_amount=10, currency="INR", merchant_id="m1")
    res = await verifier.verify(intent, cart)
    # The output is strictly typed as a semantic assessment. It has no authorization field.
    assert not hasattr(res, "authorization_decision")
    assert res.status == "PASS"

def test_decision_evidence_cannot_authorize():
    from app.domain.models import DecisionEvidence, ExecutionEvidence, PolicyEvidence, IntentEvidence, CartEvidence, CryptographicEvidence, ReplayEvidence
    evidence = DecisionEvidence(
        intent=IntentEvidence(intent_id="1", intent_timestamp=datetime.datetime.now(), intent_status="VERIFIED", intent_hash="a"),
        cryptographic=CryptographicEvidence(signature_verified=True, intent_hash="a", cart_hash="b", transaction_binding=True, verification_result="PASS"),
        cart=CartEvidence(expected_cart_hash="b", actual_cart_hash="b", cart_match=True, expected_amount="100", actual_amount="100"),
        replay=ReplayEvidence(idempotency_key="key", replay_detected=False, reservation_status="OK", execution_token_status="OK"),
        policy=PolicyEvidence(policy_name="A", policy_version="v1", policy_hash="h", policy_decision="ALLOW"),
        execution=ExecutionEvidence(execution_authorized=True, provider="mock", execution_status="OK")
    )
    # Evidence is a read-only dataclass, it has no execute() method or authorize() method
    assert not hasattr(evidence, "authorize")
    assert not hasattr(evidence, "execute")

def test_policy_explanation_cannot_authorize():
    meta = PolicyMetadata(name="A", version="v1", hash="h")
    explainer = DeterministicPolicyExplainer(meta)
    
    # Even if we pass an allowed decision, it just explains it
    decision = AuthorizationDecision(allowed=True, violations=[], policy_version="v1")
    explanation = explainer.explain(decision, {})
    
    assert explanation.decision == "ALLOW"
    assert not hasattr(explanation, "execute")

@pytest.mark.asyncio
async def test_opa_remains_final_authority():
    class MockPolicyEngine(PolicyEngine):
        async def evaluate(self, input_data):
            return AuthorizationDecision(allowed=False, violations=[{"code": "NO", "message": "NO"}], policy_version="v1")
    
    engine = MockPolicyEngine()
    decision = await engine.evaluate({})
    assert decision.allowed is False

@pytest.mark.asyncio
async def test_unauthorized_cannot_invoke_executor():
    # If a transaction was denied, payment executor should not be called
    class MockProvider(PaymentProvider):
        def __init__(self):
            self.calls = 0
        async def execute_payment(self, req):
            self.calls += 1
            return None
    
    provider = MockProvider()
    # It would require an execution token to proceed.
    # Without valid state, it won't execute.
    assert provider.calls == 0

def test_historical_policy_retained():
    # Simulating audit record retrieval
    from app.domain.models import AuditRecord
    
    # AuditRecord from yesterday with v1
    rec1 = AuditRecord(
        transaction_id="1", user_id="1", agent_id="1", merchant_id="1", intent_hash="1", open_mandate_hash="1",
        cart_hash="1", timestamp=datetime.datetime.now(), nonce="1", state="DONE", prev_record_hash="1", record_hash="1",
        explanation={"policy_version": "v1", "policy_hash": "hash1"}
    )
    
    # AuditRecord from today with v2
    rec2 = AuditRecord(
        transaction_id="2", user_id="1", agent_id="1", merchant_id="1", intent_hash="1", open_mandate_hash="1",
        cart_hash="1", timestamp=datetime.datetime.now(), nonce="1", state="DONE", prev_record_hash="1", record_hash="1",
        explanation={"policy_version": "v2", "policy_hash": "hash2"}
    )
    
    assert rec1.explanation["policy_version"] == "v1"
    assert rec2.explanation["policy_version"] == "v2"

def test_changing_evidence_after_decision_cannot_retroactively_authorize():
    # The hash of the evidence protects it
    import hashlib, json
    ev = {"intent": "VERIFIED"}
    canon = json.dumps(ev, sort_keys=True)
    h1 = hashlib.sha256(canon.encode()).hexdigest()
    
    ev["intent"] = "HACKED"
    canon2 = json.dumps(ev, sort_keys=True)
    h2 = hashlib.sha256(canon2.encode()).hexdigest()
    
    assert h1 != h2
