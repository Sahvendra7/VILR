import razorpay
import httpx
import logging
import time
import asyncio
from datetime import datetime, timezone
from app.domain.interfaces import PaymentProvider
from app.domain.models import ExecutionRequest, ExecutionReceipt
from app.config.settings import settings

logger = logging.getLogger(__name__)

class RazorpayPaymentProvider(PaymentProvider):
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )
        self.payment_call_count = 0
        self.injected_timeout_after_acceptance = False

    async def execute_payment(self, request: ExecutionRequest) -> ExecutionReceipt:
        self.payment_call_count += 1
        
        loop = asyncio.get_event_loop()
        
        try:
            amount_in_paise = int(float(request.amount) * 100)
            
            def create_order():
                data = {
                    "amount": amount_in_paise,
                    "currency": request.currency,
                    "receipt": request.transaction_id[:40],
                    "notes": {
                        "merchant_id": request.merchant_id,
                        "vilr_mandate_hash": request.mandate_hash,
                        "vilr_idempotency_key": request.idempotency_key
                    }
                }
                return self.client.order.create(data=data)
            
            if self.injected_timeout_after_acceptance:
                logger.error("SIMULATED TIMEOUT: Razorpay provider timeout injected.")
                raise httpx.ReadTimeout("Simulated read timeout")
                
            t0 = time.time()
            order = await loop.run_in_executor(None, create_order)
            latency = (time.time() - t0) * 1000
            
            provider_id = order.get("id")
            
            logger.info(f"RAZORPAY_ORDER_CREATED id={provider_id} latency={latency:.0f}ms")
            
            return ExecutionReceipt(
                transaction_id=request.transaction_id,
                provider_transaction_id=provider_id,
                status="SUCCESS",
                timestamp=datetime.now(timezone.utc)
            )
            
        except httpx.TimeoutException:
            return ExecutionReceipt(
                transaction_id=request.transaction_id,
                status="UNKNOWN",
                timestamp=datetime.now(timezone.utc),
                error_message="Network timeout waiting for Razorpay"
            )
        except Exception as e:
            logger.error(f"RAZORPAY_ERROR error='{str(e)}'")
            return ExecutionReceipt(
                transaction_id=request.transaction_id,
                status="FAILED",
                timestamp=datetime.now(timezone.utc),
                error_message=str(e)
            )
