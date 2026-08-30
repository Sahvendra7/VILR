from typing import Optional
from app.domain.interfaces import PaymentProvider
from app.domain.models import ExecutionRequest, ExecutionReceipt
from app.domain.state_machine import StateController, TransactionState
from app.domain.errors import InvalidStateTransition, PaymentExecutionFailed, PaymentProviderError, IdempotencyConflict

class PaymentExecutor:
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    async def execute(self, request: ExecutionRequest, state_controller: StateController) -> ExecutionReceipt:
        # 1. Validate authorization state
        if state_controller.current_state != TransactionState.RESERVATION_COMMITTED:
            raise InvalidStateTransition("Payment can only be executed after reservation is committed")

        # 2. Transition to EXECUTION_STARTED
        state_controller.transition_to(TransactionState.EXECUTION_STARTED)

        # 3. Call Provider
        try:
            receipt = await self.provider.execute_payment(request)
        except IdempotencyConflict:
            state_controller.transition_to(TransactionState.PAYMENT_FAILED)
            raise
        except PaymentProviderError as e:
            state_controller.transition_to(TransactionState.PAYMENT_FAILED)
            raise PaymentExecutionFailed(str(e)) from e
        except Exception as e:
            # Any unhandled exception maps to FAILED or UNKNOWN, but let's be conservative
            state_controller.transition_to(TransactionState.PAYMENT_FAILED)
            raise PaymentExecutionFailed("Internal execution failure") from e

        # 4. Handle Result
        if receipt.status == "SUCCESS":
            state_controller.transition_to(TransactionState.PAYMENT_CONFIRMED)
        elif receipt.status == "FAILED":
            state_controller.transition_to(TransactionState.PAYMENT_FAILED)
        elif receipt.status == "UNKNOWN":
            state_controller.transition_to(TransactionState.PAYMENT_UNKNOWN)
        else:
            state_controller.transition_to(TransactionState.PAYMENT_FAILED)
            raise PaymentExecutionFailed(f"Unknown status: {receipt.status}")

        return receipt

    async def reconcile(self, idempotency_key: str, state_controller: StateController) -> Optional[ExecutionReceipt]:
        if state_controller.current_state != TransactionState.PAYMENT_UNKNOWN:
            raise InvalidStateTransition("Can only reconcile from PAYMENT_UNKNOWN")

        if not hasattr(self.provider, "get_payment_status"):
            raise NotImplementedError("Provider does not support get_payment_status")
            
        receipt = await self.provider.get_payment_status(idempotency_key)
        if not receipt:
            return None
            
        if receipt.status == "SUCCESS":
            state_controller.transition_to(TransactionState.PAYMENT_CONFIRMED)
        elif receipt.status == "FAILED":
            state_controller.transition_to(TransactionState.PAYMENT_FAILED)
            
        return receipt
