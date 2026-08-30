import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, UTC
from uuid import uuid4

from app.domain.models import ExecutionRequest, ExecutionReceipt
from app.domain.state_machine import StateController, TransactionState
from app.domain.errors import InvalidStateTransition, IdempotencyConflict, PaymentExecutionFailed

from adapters.razorpay.provider import MockRazorpayProvider
from app.execution.executor import PaymentExecutor

@pytest.fixture
def provider():
    return MockRazorpayProvider()

@pytest.fixture
def executor(provider):
    return PaymentExecutor(provider)

def create_valid_request(override_key=None, override_amount="4999.00", override_merchant="merchant_123"):
    return ExecutionRequest(
        transaction_id=f"txn_{uuid4().hex[:8]}",
        idempotency_key=override_key or f"idem_{uuid4().hex[:8]}",
        merchant_id=override_merchant,
        amount=Decimal(override_amount),
        currency="INR",
        payment_method_id="pm_123",
        mandate_hash="hash_123"
    )

def create_ready_state():
    state = StateController()
    state.current_state = TransactionState.RESERVATION_COMMITTED
    return state

@pytest.mark.asyncio
async def test_pa_01_successful_payment(executor):
    request = create_valid_request()
    state = create_ready_state()
    
    receipt = await executor.execute(request, state)
    
    assert receipt.status == "SUCCESS"
    assert receipt.provider_transaction_id is not None
    assert state.current_state == TransactionState.PAYMENT_CONFIRMED

@pytest.mark.asyncio
async def test_pa_02_confirmed_provider_failure(executor, provider):
    provider.injected_outcome = "FAILED"
    request = create_valid_request()
    state = create_ready_state()
    
    receipt = await executor.execute(request, state)
    
    assert receipt.status == "FAILED"
    assert receipt.error_message == "INSUFFICIENT_FUNDS"
    assert state.current_state == TransactionState.PAYMENT_FAILED

@pytest.mark.asyncio
async def test_pa_03_provider_timeout_to_unknown(executor, provider):
    provider.injected_timeout_after_acceptance = True
    request = create_valid_request()
    state = create_ready_state()
    
    receipt = await executor.execute(request, state)
    
    assert receipt.status == "UNKNOWN"
    assert state.current_state == TransactionState.PAYMENT_UNKNOWN

@pytest.mark.asyncio
async def test_pa_04_reconciliation_unknown_to_success(executor, provider):
    provider.injected_timeout_after_acceptance = True
    request = create_valid_request()
    state = create_ready_state()
    
    await executor.execute(request, state)
    assert state.current_state == TransactionState.PAYMENT_UNKNOWN
    
    # Provider actually stored it as SUCCESS originally
    receipt = await executor.reconcile(request.idempotency_key, state)
    
    assert receipt.status == "SUCCESS"
    assert state.current_state == TransactionState.PAYMENT_CONFIRMED

@pytest.mark.asyncio
async def test_pa_05_reconciliation_unknown_to_failed(executor, provider):
    provider.injected_timeout_after_acceptance = True
    provider.injected_outcome = "FAILED"
    
    request = create_valid_request()
    state = create_ready_state()
    
    await executor.execute(request, state)
    assert state.current_state == TransactionState.PAYMENT_UNKNOWN
    
    receipt = await executor.reconcile(request.idempotency_key, state)
    
    assert receipt.status == "FAILED"
    assert state.current_state == TransactionState.PAYMENT_FAILED

@pytest.mark.asyncio
async def test_pa_06_same_idempotency_key_no_duplicate(executor):
    request = create_valid_request()
    state1 = create_ready_state()
    
    receipt1 = await executor.execute(request, state1)
    
    state2 = create_ready_state()
    receipt2 = await executor.execute(request, state2)
    
    assert receipt1.provider_transaction_id == receipt2.provider_transaction_id
    assert receipt2.status == "SUCCESS"

@pytest.mark.asyncio
async def test_pa_07_same_key_different_amount_conflict(executor):
    key = "idem_conflict_amount"
    req1 = create_valid_request(override_key=key, override_amount="100.00")
    req2 = create_valid_request(override_key=key, override_amount="200.00")
    
    await executor.execute(req1, create_ready_state())
    
    with pytest.raises(IdempotencyConflict):
        await executor.execute(req2, create_ready_state())

@pytest.mark.asyncio
async def test_pa_08_same_key_different_currency_conflict(executor):
    key = "idem_conflict_curr"
    req1 = create_valid_request(override_key=key)
    req2 = create_valid_request(override_key=key)
    req2.currency = "USD"
    
    await executor.execute(req1, create_ready_state())
    
    with pytest.raises(IdempotencyConflict):
        await executor.execute(req2, create_ready_state())

@pytest.mark.asyncio
async def test_pa_09_same_key_different_merchant_conflict(executor):
    key = "idem_conflict_merchant"
    req1 = create_valid_request(override_key=key, override_merchant="merch_1")
    req2 = create_valid_request(override_key=key, override_merchant="merch_2")
    
    await executor.execute(req1, create_ready_state())
    
    with pytest.raises(IdempotencyConflict):
        await executor.execute(req2, create_ready_state())

@pytest.mark.asyncio
async def test_pa_10_concurrent_duplicate_execution(executor, provider):
    provider.simulate_network_delay = 0.1
    key = "idem_concurrent"
    
    req1 = create_valid_request(override_key=key)
    req2 = create_valid_request(override_key=key)
    
    state1 = create_ready_state()
    state2 = create_ready_state()
    
    r1, r2 = await asyncio.gather(
        executor.execute(req1, state1),
        executor.execute(req2, state2)
    )
    
    assert r1.provider_transaction_id == r2.provider_transaction_id

@pytest.mark.asyncio
async def test_pa_11_unauthorized_execution_rejected(executor):
    request = create_valid_request()
    state = StateController() # defaults to INTENT_RECEIVED
    
    with pytest.raises(InvalidStateTransition):
        await executor.execute(request, state)

@pytest.mark.asyncio
async def test_pa_12_expired_execution_authorization_rejected(executor):
    request = create_valid_request()
    state = StateController()
    state.current_state = TransactionState.MANDATE_EXPIRED
    
    with pytest.raises(InvalidStateTransition):
        await executor.execute(request, state)

@pytest.mark.asyncio
async def test_pa_13_malformed_execution_request_rejected(executor):
    with pytest.raises(ValueError):
        # Pydantic will reject invalid money format
        ExecutionRequest(
            transaction_id="txn_1",
            idempotency_key="idem_1",
            merchant_id="m_1",
            amount=Decimal("-10.0"),
            currency="INR",
            payment_method_id="pm_1",
            mandate_hash="hash"
        )

@pytest.mark.asyncio
async def test_pa_14_provider_unavailable(executor, provider):
    provider.injected_network_failure = True
    request = create_valid_request()
    state = create_ready_state()
    
    with pytest.raises(PaymentExecutionFailed):
        await executor.execute(request, state)
        
    assert state.current_state == TransactionState.PAYMENT_FAILED

@pytest.mark.asyncio
async def test_pa_15_payment_id_remains_stable_across_idempotent_replay(executor):
    request = create_valid_request()
    
    state1 = create_ready_state()
    receipt1 = await executor.execute(request, state1)
    
    state2 = create_ready_state()
    receipt2 = await executor.execute(request, state2)
    
    assert receipt1.provider_transaction_id == receipt2.provider_transaction_id
    assert receipt1.status == receipt2.status

@pytest.mark.asyncio
async def test_reconcile_invalid_state_transition(executor):
    state = create_ready_state()
    with pytest.raises(InvalidStateTransition):
        await executor.reconcile("some_key", state)
