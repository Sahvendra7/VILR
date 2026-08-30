from enum import Enum
from app.domain.errors import InvalidStateTransition

class TransactionState(str, Enum):
    INTENT_RECEIVED = "INTENT_RECEIVED"
    AP2_VERIFIED = "AP2_VERIFIED"
    CART_VERIFIED = "CART_VERIFIED"
    RESERVATION_ACQUIRED = "RESERVATION_ACQUIRED"
    SEMANTIC_ANALYZED = "SEMANTIC_ANALYZED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    AUTHORIZED = "AUTHORIZED"
    RESERVATION_COMMITTED = "RESERVATION_COMMITTED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_UNKNOWN = "PAYMENT_UNKNOWN"
    # Failure states (terminal)
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    HASH_MISMATCH = "HASH_MISMATCH"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    SEMANTIC_DRIFT = "SEMANTIC_DRIFT"
    POLICY_DENIED = "POLICY_DENIED"
    MANDATE_EXPIRED = "MANDATE_EXPIRED"
    MERCHANT_UNTRUSTED = "MERCHANT_UNTRUSTED"
    DUPLICATE_EXECUTION = "DUPLICATE_EXECUTION"

VALID_TRANSITIONS = {
    TransactionState.INTENT_RECEIVED: [TransactionState.AP2_VERIFIED, TransactionState.INVALID_SIGNATURE, TransactionState.MANDATE_EXPIRED],
    TransactionState.AP2_VERIFIED: [TransactionState.CART_VERIFIED, TransactionState.HASH_MISMATCH, TransactionState.MERCHANT_UNTRUSTED],
    TransactionState.CART_VERIFIED: [TransactionState.RESERVATION_ACQUIRED, TransactionState.REPLAY_DETECTED],
    TransactionState.RESERVATION_ACQUIRED: [TransactionState.SEMANTIC_ANALYZED, TransactionState.SEMANTIC_DRIFT],
    TransactionState.SEMANTIC_ANALYZED: [TransactionState.POLICY_EVALUATED, TransactionState.POLICY_DENIED],
    TransactionState.POLICY_EVALUATED: [TransactionState.AUTHORIZED, TransactionState.POLICY_DENIED],
    TransactionState.AUTHORIZED: [TransactionState.RESERVATION_COMMITTED],
    TransactionState.RESERVATION_COMMITTED: [TransactionState.EXECUTION_STARTED, TransactionState.DUPLICATE_EXECUTION],
    TransactionState.EXECUTION_STARTED: [TransactionState.PAYMENT_CONFIRMED, TransactionState.PAYMENT_FAILED, TransactionState.PAYMENT_UNKNOWN],
    TransactionState.PAYMENT_UNKNOWN: [TransactionState.PAYMENT_CONFIRMED, TransactionState.PAYMENT_FAILED],
}

# Fill terminal states with empty lists
for state in TransactionState:
    if state not in VALID_TRANSITIONS:
        VALID_TRANSITIONS[state] = []

class StateController:
    def __init__(self, initial_state: TransactionState = TransactionState.INTENT_RECEIVED):
        self.current_state = initial_state

    def transition_to(self, new_state: TransactionState) -> None:
        allowed = VALID_TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed:
            raise InvalidStateTransition(f"Cannot transition from {self.current_state} to {new_state}")
        self.current_state = new_state
