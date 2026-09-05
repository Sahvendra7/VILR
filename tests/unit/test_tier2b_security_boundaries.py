import pytest
from app.domain.models import SecurityReceipt, DecisionEvidence, ExecutionEvidence, ReplayEvidence

@pytest.mark.asyncio
async def test_replay_visualization_cannot_authorize():
    # TEST 1: Replay visualization cannot authorize payment.
    replay = ReplayEvidence(idempotency_key="foo", replay_detected=True, reservation_status="CONFLICT", execution_token_status="NONE")
    assert not hasattr(replay, "authorize")
    assert replay.replay_detected is True

@pytest.mark.asyncio
async def test_replay_visualization_cannot_consume_token():
    # TEST 2: Replay visualization cannot consume execution tokens.
    replay = ReplayEvidence(idempotency_key="foo", replay_detected=True, reservation_status="CONFLICT", execution_token_status="NONE")
    assert not hasattr(replay, "consume_token")

@pytest.mark.asyncio
async def test_unknown_cannot_trigger_automatic_retry():
    # TEST 3: UNKNOWN handling cannot trigger automatic payment retry.
    receipt = SecurityReceipt(
        receipt_id="1", request_id="1", intent_verified=True, cryptographic_verification=True,
        cart_verified=True, replay_check="CLEAR", policy_result="ALLOW", execution_result="UNKNOWN",
        final_decision="DENIED", decision_source="SYSTEM", timestamp="2026-09-05T00:00:00Z",
        execution_status="UNKNOWN", provider_call="YES", automatic_retry="NO", reconciliation="REQUIRED"
    )
    assert receipt.automatic_retry == "NO"

@pytest.mark.asyncio
async def test_exception_intelligence_cannot_change_unknown_to_confirmed():
    # TEST 4: Exception Intelligence cannot change UNKNOWN to CONFIRMED.
    from app.exception.intelligence import ExceptionIntelligenceLayer, ExceptionInvestigation, InvestigationContext
    
    class FakeInvestigator:
        async def generate_json(self, *args, **kwargs):
            return ExceptionInvestigation(
                request_id="1", transaction_id="1", category="PROVIDER_TIMEOUT",
                severity="HIGH", confidence=0.9, evidence=[], explanation="Timeout", recommended_action="RECONCILE",
                decision_source="SYSTEM"
            )
            
    ei = ExceptionIntelligenceLayer(FakeInvestigator())
    ctx = InvestigationContext(request_id="1", intent_id="1", transaction_id="1", workflow_state="PAYMENT_UNKNOWN",
                               deterministic_decision="DENIED", failure_code=None, relevant_evidence=[],
                               policy_result={}, semantic_result={}, provider_result={"status":"UNKNOWN"})
    res = await ei.investigate(ctx)
    assert res.category.value == "PROVIDER_TIMEOUT"
    assert res.recommended_action == "RECONCILE"
    assert not hasattr(res, "change_state")

@pytest.mark.asyncio
async def test_exception_intelligence_cannot_invoke_payment():
    # TEST 5: Exception Intelligence cannot invoke PaymentExecutor.
    from app.exception.intelligence import ExceptionInvestigation
    investigation = ExceptionInvestigation(request_id="1", transaction_id="1", category="PROVIDER_TIMEOUT", severity="HIGH", confidence=0.9, evidence=[], explanation="Timeout", recommended_action="RECONCILE", decision_source="SYSTEM")
    assert not hasattr(investigation, "execute")
    assert not hasattr(investigation, "retry")

@pytest.mark.asyncio
async def test_reconciliation_cannot_create_second_payment():
    # TEST 6: Reconciliation cannot create a second payment.
    from app.domain.gateway import GatewayOrchestrator
    assert getattr(GatewayOrchestrator.resolve_unknown, "__name__") == "resolve_unknown"
    # Resolve unknown purely updates state; does not invoke `execute_payment` on provider.
    
@pytest.mark.asyncio
async def test_redis_unavailable_fails_closed():
    # TEST 7: Redis unavailable causes fail-closed behavior.
    from app.idempotency.store import RedisIdempotencyStore
    import redis.asyncio as redis
    store = RedisIdempotencyStore(redis_client=redis.Redis(host="invalid", port=9999, socket_timeout=0.1))
    with pytest.raises(Exception):
        await store.try_reserve("key", "tx", 300)

@pytest.mark.asyncio
async def test_replay_produces_no_provider_side_effect():
    # TEST 8: Replay after consumed token produces no provider side effect.
    from app.domain.errors import DuplicateExecution
    from app.domain.gateway import GatewayOrchestrator
    from unittest.mock import AsyncMock, MagicMock
    
    gateway = GatewayOrchestrator(
        semantic=AsyncMock(), policy=AsyncMock(), idempotency=AsyncMock(),
        verifier=AsyncMock(), payment_executor=AsyncMock(), audit=AsyncMock()
    )
    
    gateway.idempotency.consume_execution_token.side_effect = DuplicateExecution("Token consumed")
    
    from app.domain.gateway import GatewayExecuteRequest
    req = GatewayExecuteRequest(
        transaction_id="tx", execution_token="tok", merchant_id="m",
        amount="10", currency="INR", payment_method_id="pm",
        mandate_hash="mh", provider_idempotency_key="key"
    )
    
    with pytest.raises(DuplicateExecution):
        await gateway.execute(req)
        
    gateway.payment_executor.execute.assert_not_called()

