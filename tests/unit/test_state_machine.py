import pytest
from app.domain.state_machine import StateController, TransactionState
from app.domain.errors import InvalidStateTransition

def test_normal_success_path():
    sm = StateController()
    assert sm.current_state == TransactionState.INTENT_RECEIVED

    sm.transition_to(TransactionState.AP2_VERIFIED)
    sm.transition_to(TransactionState.CART_VERIFIED)
    sm.transition_to(TransactionState.RESERVATION_ACQUIRED)
    sm.transition_to(TransactionState.SEMANTIC_ANALYZED)
    sm.transition_to(TransactionState.POLICY_EVALUATED)
    sm.transition_to(TransactionState.AUTHORIZED)
    sm.transition_to(TransactionState.RESERVATION_COMMITTED)
    sm.transition_to(TransactionState.EXECUTION_STARTED)
    sm.transition_to(TransactionState.PAYMENT_CONFIRMED)

def test_invalid_transition():
    sm = StateController(TransactionState.INTENT_RECEIVED)
    with pytest.raises(InvalidStateTransition):
        sm.transition_to(TransactionState.CART_VERIFIED)

def test_terminal_state():
    sm = StateController(TransactionState.POLICY_DENIED)
    with pytest.raises(InvalidStateTransition):
        sm.transition_to(TransactionState.AUTHORIZED)

def test_payment_unknown_recovery():
    sm = StateController(TransactionState.EXECUTION_STARTED)
    sm.transition_to(TransactionState.PAYMENT_UNKNOWN)

    with pytest.raises(InvalidStateTransition):
        sm.transition_to(TransactionState.RESERVATION_COMMITTED) # Cannot go back

    sm.transition_to(TransactionState.PAYMENT_CONFIRMED) # Valid manual reconciliation

def test_payment_unknown_failure():
    sm = StateController(TransactionState.PAYMENT_UNKNOWN)
    sm.transition_to(TransactionState.PAYMENT_FAILED)

def test_various_failures():
    paths = [
        (TransactionState.INTENT_RECEIVED, TransactionState.INVALID_SIGNATURE),
        (TransactionState.INTENT_RECEIVED, TransactionState.MANDATE_EXPIRED),
        (TransactionState.AP2_VERIFIED, TransactionState.HASH_MISMATCH),
        (TransactionState.AP2_VERIFIED, TransactionState.MERCHANT_UNTRUSTED),
        (TransactionState.CART_VERIFIED, TransactionState.REPLAY_DETECTED),
        (TransactionState.RESERVATION_ACQUIRED, TransactionState.SEMANTIC_DRIFT),
        (TransactionState.SEMANTIC_ANALYZED, TransactionState.POLICY_DENIED),
        (TransactionState.POLICY_EVALUATED, TransactionState.POLICY_DENIED),
        (TransactionState.RESERVATION_COMMITTED, TransactionState.DUPLICATE_EXECUTION),
        (TransactionState.EXECUTION_STARTED, TransactionState.PAYMENT_FAILED),
    ]
    for start, fail in paths:
        sm = StateController(start)
        sm.transition_to(fail)
