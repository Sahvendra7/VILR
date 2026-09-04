import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, UTC
from uuid import uuid4

from app.domain.gateway import GatewayOrchestrator, GatewayAuthorizeRequest, GatewayExecuteRequest
from app.domain.state_machine import TransactionState
from app.domain.models import (
    ClosedCheckoutMandate,
    ExecutionReceipt, UserIntent, Cart, CartItem, HardConstraints, SoftPreferences
)
from app.domain.errors import (
    InvalidStateTransition, MandateExpired, InvalidSignature, HashMismatch,
    MerchantUntrusted, ReplayDetected, SemanticDrift, PolicyDenied,
    PaymentUnknown, DuplicateExecution, InvalidRequest
)

@pytest.fixture
def mock_verifier():
    verifier = AsyncMock()
    open_mandate = MagicMock()
    open_mandate.constraints.model_dump.return_value = {}
    closed_mandate = MagicMock()
    closed_mandate.open_mandate_hash = "omh_123"
    closed_mandate.cart_hash = "ch_123"
    verifier.verify_open_checkout_mandate.return_value = open_mandate
    verifier.verify_closed_checkout_mandate.return_value = closed_mandate
    return verifier

@pytest.fixture
def mock_idempotency():
    idem = AsyncMock()
    idem.try_reserve.return_value = True
    return idem

@pytest.fixture
def mock_semantic():
    sem = AsyncMock()
    res = MagicMock()
    res.status = "PASS"
    res.confidence = 0.99
    sem.verify.return_value = res
    return sem

@pytest.fixture
def mock_policy():
    pol = AsyncMock()
    dec = MagicMock()
    dec.allowed = True
    dec.violations = []
    dec.policy_version = "v1"
    pol.evaluate.return_value = dec
    return pol

@pytest.fixture
def mock_executor():
    exec = AsyncMock()
    rec = ExecutionReceipt(
        transaction_id="tx_123",
        provider_transaction_id="pay_123",
        status="SUCCESS",
        timestamp=datetime.now(UTC)
    )
    exec.execute.return_value = rec
    exec.reconcile.return_value = rec
    return exec

@pytest.fixture
def mock_audit():
    audit = AsyncMock()
    audit.get.return_value = None
    return audit

@pytest.fixture
def gateway(mock_verifier, mock_idempotency, mock_semantic, mock_policy, mock_executor, mock_audit, monkeypatch):
    monkeypatch.setattr('app.domain.gateway.compute_checkout_hash', lambda x: 'ch_123')
    
    # Store tokens in a local dict for the mock to use
    fake_tokens = {}
    async def create_token(token, tx_id, auth_data, ttl):
        fake_tokens[token] = {"transaction_id": tx_id, "auth_data": auth_data, "status": "available"}
        
    async def consume_token(token, tx_id, expected_amount, expected_currency, expected_merchant, expected_hash):
        if token not in fake_tokens: raise ValueError("Invalid or expired execution token")
        if fake_tokens[token]["transaction_id"] != tx_id:
            from app.domain.errors import InvalidRequest
            raise InvalidRequest("Token transaction mismatch")
        if fake_tokens[token]["status"] == "consumed":
            from app.domain.errors import DuplicateExecution
            raise DuplicateExecution("Execution token already consumed")
        fake_tokens[token]["status"] = "consumed"
        return fake_tokens[token]["auth_data"]
        
    mock_idempotency.create_execution_token.side_effect = create_token
    mock_idempotency.consume_execution_token.side_effect = consume_token
    return GatewayOrchestrator(
        verifier=mock_verifier,
        idempotency=mock_idempotency,
        semantic=mock_semantic,
        policy=mock_policy,
        payment_executor=mock_executor,
        audit=mock_audit
    )

def create_auth_request():
    return GatewayAuthorizeRequest(
        transaction_id="tx_123",
        open_checkout_token="open_tok",
        closed_checkout_token="closed_tok",
        user_intent=UserIntent(
            user_id="u1", raw_prompt="buy laptop", semantic_intent="laptop",
            hard_constraints=HardConstraints(max_budget=Decimal("100"), currency="USD"),
            soft_preferences=SoftPreferences()
        ),
        cart=Cart(
            items=[], total_amount=Decimal("50.0"), currency="USD", merchant_id="m1"
        ),
        user_public_key={},
        merchant_public_key={}
    )

@pytest.mark.asyncio
async def test_g_01_valid_authorization(gateway):
    req = create_auth_request()
    res = await gateway.authorize(req)
    assert res["status"] == "AUTHORIZED"
    assert "execution_token" in res

@pytest.mark.asyncio
async def test_g_02_invalid_signature(gateway, mock_verifier):
    mock_verifier.verify_open_checkout_mandate.side_effect = InvalidSignature("Bad sig")
    req = create_auth_request()
    with pytest.raises(InvalidSignature):
        await gateway.authorize(req)

@pytest.mark.asyncio
async def test_g_03_hash_mismatch(gateway, mock_verifier):
    mock_verifier.verify_closed_checkout_mandate.return_value = ClosedCheckoutMandate(
        mandate_id="m_123",
        open_mandate_hash="omh_123",
        merchant_id="m1",
        cart_hash="ch_123_bad",
        signature="sig"
    )
    req = create_auth_request()
    with pytest.raises(HashMismatch):
        await gateway.authorize(req)

@pytest.mark.asyncio
async def test_g_04_expired_mandate(gateway, mock_verifier):
    mock_verifier.verify_open_checkout_mandate.side_effect = MandateExpired("Expired")
    req = create_auth_request()
    with pytest.raises(MandateExpired):
        await gateway.authorize(req)

@pytest.mark.asyncio
async def test_g_05_merchant_untrusted(gateway, mock_verifier):
    mock_verifier.verify_closed_checkout_mandate.side_effect = MerchantUntrusted("Untrusted")
    req = create_auth_request()
    with pytest.raises(MerchantUntrusted):
        await gateway.authorize(req)

@pytest.mark.asyncio
async def test_g_06_replay(gateway, mock_idempotency):
    mock_idempotency.try_reserve.return_value = False
    req = create_auth_request()
    with pytest.raises(ReplayDetected):
        await gateway.authorize(req)

@pytest.mark.asyncio
async def test_g_07_semantic_failure_releases_reservation(gateway, mock_semantic, mock_idempotency):
    res = MagicMock()
    res.status = "FAIL"
    res.confidence = 0.1
    mock_semantic.verify.return_value = res
    
    req = create_auth_request()
    with pytest.raises(SemanticDrift):
        await gateway.authorize(req)
    mock_idempotency.release.assert_called_once()

@pytest.mark.asyncio
async def test_g_08_policy_denial_releases_reservation(gateway, mock_policy, mock_idempotency):
    dec = MagicMock()
    dec.allowed = False
    mock_policy.evaluate.return_value = dec
    
    req = create_auth_request()
    with pytest.raises(PolicyDenied):
        await gateway.authorize(req)
    mock_idempotency.release.assert_called_once()

@pytest.mark.asyncio
async def test_g_09_llm_pass_cannot_bypass_opa(gateway, mock_semantic, mock_policy):
    sem_res = MagicMock()
    sem_res.status = "PASS" # LLM says pass
    mock_semantic.verify.return_value = sem_res
    
    dec = MagicMock()
    dec.allowed = False # OPA says no
    mock_policy.evaluate.return_value = dec
    
    req = create_auth_request()
    with pytest.raises(PolicyDenied):
        await gateway.authorize(req)

@pytest.mark.asyncio
async def test_g_10_opa_denial_blocks_execution(gateway, mock_policy):
    dec = MagicMock()
    dec.allowed = False
    mock_policy.evaluate.return_value = dec
    
    req = create_auth_request()
    with pytest.raises(PolicyDenied):
        await gateway.authorize(req)
    # Never reaches execution token generation

@pytest.mark.asyncio
async def test_g_11_only_committed_authorization_can_execute(gateway):
    exec_req = GatewayExecuteRequest(
        transaction_id="tx_123", execution_token="fake", amount=50.0,
        currency="USD", merchant_id="m1", mandate_hash="omh_123",
        provider_idempotency_key="pid", payment_method_id="pm1"
    )
    with pytest.raises(InvalidRequest):
        await gateway.execute(exec_req)

@pytest.mark.asyncio
async def test_g_12_execution_token_invalid_before_authorization(gateway):
    req = create_auth_request()
    # Before auth...
    exec_req = GatewayExecuteRequest(
        transaction_id="tx_123", execution_token="invalid", amount=50.0,
        currency="USD", merchant_id="m1", mandate_hash="omh_123",
        provider_idempotency_key="pid", payment_method_id="pm1"
    )
    with pytest.raises(InvalidRequest):
        await gateway.execute(exec_req)

@pytest.mark.asyncio
async def test_g_13_execution_token_single_use(gateway):
    req = create_auth_request()
    res = await gateway.authorize(req)
    
    exec_req = GatewayExecuteRequest(
        transaction_id="tx_123", execution_token=res["execution_token"], amount=50.0,
        currency="USD", merchant_id="m1", mandate_hash="omh_123",
        provider_idempotency_key="pid", payment_method_id="pm1"
    )
    await gateway.execute(exec_req)
    
    # Second time should fail
    from app.domain.errors import DuplicateExecution
    with pytest.raises(DuplicateExecution):
        await gateway.execute(exec_req)

@pytest.mark.asyncio
async def test_g_14_payment_success(gateway):
    req = create_auth_request()
    res = await gateway.authorize(req)
    
    exec_req = GatewayExecuteRequest(
        transaction_id="tx_123", execution_token=res["execution_token"], amount=50.0,
        currency="USD", merchant_id="m1", mandate_hash="omh_123",
        provider_idempotency_key="pid", payment_method_id="pm1"
    )
    exec_res = await gateway.execute(exec_req)
    assert exec_res["status"] == "SUCCESS"

@pytest.mark.asyncio
async def test_g_15_payment_failure(gateway, mock_executor):
    req = create_auth_request()
    res = await gateway.authorize(req)
    
    fail_rec = ExecutionReceipt(
        transaction_id="tx_123", status="FAILED", timestamp=datetime.now(UTC)
    )
    mock_executor.execute.return_value = fail_rec
    
    exec_req = GatewayExecuteRequest(
        transaction_id="tx_123", execution_token=res["execution_token"], amount=50.0,
        currency="USD", merchant_id="m1", mandate_hash="omh_123",
        provider_idempotency_key="pid", payment_method_id="pm1"
    )
    exec_res = await gateway.execute(exec_req)
    assert exec_res["status"] == "FAILED"

@pytest.mark.asyncio
async def test_g_16_payment_unknown(gateway, mock_executor):
    req = create_auth_request()
    res = await gateway.authorize(req)
    
    unk_rec = ExecutionReceipt(
        transaction_id="tx_123", status="UNKNOWN", timestamp=datetime.now(UTC)
    )
    mock_executor.execute.return_value = unk_rec
    
    exec_req = GatewayExecuteRequest(
        transaction_id="tx_123", execution_token=res["execution_token"], amount=50.0,
        currency="USD", merchant_id="m1", mandate_hash="omh_123",
        provider_idempotency_key="pid", payment_method_id="pm1"
    )
    exec_res = await gateway.execute(exec_req)
    assert exec_res["status"] == "UNKNOWN"

@pytest.mark.asyncio
async def test_g_17_unknown_reconciliation_success(gateway, mock_executor):
    req = create_auth_request()
    await gateway.authorize(req)
    
    # Fake payment unknown state setup
    gateway._tx_states["tx_123"].current_state = TransactionState.PAYMENT_UNKNOWN
    
    succ_rec = ExecutionReceipt(
        transaction_id="tx_123", status="SUCCESS", timestamp=datetime.now(UTC)
    )
    mock_executor.reconcile.return_value = succ_rec
    
    res = await gateway.resolve_unknown("tx_123", "pid")
    assert res["status"] == "SUCCESS"

@pytest.mark.asyncio
async def test_g_18_unknown_reconciliation_failure(gateway, mock_executor):
    req = create_auth_request()
    await gateway.authorize(req)
    
    gateway._tx_states["tx_123"].current_state = TransactionState.PAYMENT_UNKNOWN
    
    fail_rec = ExecutionReceipt(
        transaction_id="tx_123", status="FAILED", timestamp=datetime.now(UTC)
    )
    mock_executor.reconcile.return_value = fail_rec
    
    res = await gateway.resolve_unknown("tx_123", "pid")
    assert res["status"] == "FAILED"

@pytest.mark.asyncio
async def test_g_19_different_checkout_under_same_mandate(gateway):
    req = create_auth_request()
    res = await gateway.authorize(req)
    
    # Execute with altered amount
    exec_req = GatewayExecuteRequest(
        transaction_id="tx_123", execution_token=res["execution_token"], amount=999.0, # modified
        currency="USD", merchant_id="m1", mandate_hash="omh_123",
        provider_idempotency_key="pid", payment_method_id="pm1"
    )
    with pytest.raises(InvalidRequest):
        await gateway.execute(exec_req)

import asyncio

@pytest.mark.asyncio
async def test_g_20_concurrent_authorization(gateway, mock_idempotency):
    req = create_auth_request()
    
    async def try_auth():
        try:
            return await gateway.authorize(req)
        except ReplayDetected:
            return None

    # mock_idempotency will simulate that the first gets True, second gets False
    mock_idempotency.try_reserve.side_effect = [True, False, False]
    
    results = await asyncio.gather(try_auth(), try_auth(), try_auth())
    successes = [r for r in results if r is not None]
    
    assert len(successes) == 1
