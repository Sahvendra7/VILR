import hashlib
import json
import uuid
import asyncio
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from app.domain.interfaces import PaymentProvider
from app.domain.models import ExecutionRequest, ExecutionReceipt
from app.domain.errors import IdempotencyConflict, PaymentProviderError

class MockRazorpayProvider(PaymentProvider):
    def __init__(self, simulate_network_delay: float = 0.0):
        # idempotency_key -> record
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self.simulate_network_delay = simulate_network_delay

        # Injection points for testing
        self.injected_outcome: Optional[str] = None
        self.injected_timeout_after_acceptance: bool = False
        self.injected_network_failure: bool = False
        self.payment_call_count = 0
        self.payment_creation_count = 0

    def _fingerprint(self, request: ExecutionRequest) -> str:
        # SHA-256(canonicalized(amount, currency, merchant_id, mandate_hash))
        payload = {
            "amount": float(request.amount),
            "currency": request.currency,
            "merchant_id": request.merchant_id,
            "mandate_hash": request.mandate_hash
        }
        canonical = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    async def execute_payment(self, request: ExecutionRequest) -> ExecutionReceipt:
        self.payment_call_count += 1
        if self.simulate_network_delay > 0:
            await asyncio.sleep(self.simulate_network_delay)
            
        if self.injected_network_failure:
            raise PaymentProviderError("Connection refused by provider")

        fingerprint = self._fingerprint(request)
        key = request.idempotency_key

        async with self._lock:
            if key in self._store:
                existing = self._store[key]
                if existing["fingerprint"] != fingerprint:
                    raise IdempotencyConflict("Conflicting reuse of idempotency key with different parameters")
                
                # Replay idempotent response
                # Note: If it was UNKNOWN originally (timeout_after_acceptance), it actually succeeded/failed on the provider side.
                return ExecutionReceipt(
                    transaction_id=existing["transaction_id"],
                    provider_transaction_id=existing["payment_id"],
                    status=existing["status"],
                    timestamp=existing["created_at"],
                    error_message=existing.get("error_message")
                )

            # Process new request
            self.payment_creation_count += 1
            payment_id = f"pay_{uuid.uuid4().hex[:12]}"
            now = datetime.now(UTC)
            
            outcome = self.injected_outcome or "SUCCESS"
            error_message = None
            
            if outcome == "FAILED":
                error_message = "INSUFFICIENT_FUNDS"
            
            record = {
                "fingerprint": fingerprint,
                "transaction_id": request.transaction_id,
                "payment_id": payment_id if outcome == "SUCCESS" else None,
                "status": outcome,
                "created_at": now,
                "error_message": error_message,
                "was_timeout": self.injected_timeout_after_acceptance
            }
            
            self._store[key] = record

            if self.injected_timeout_after_acceptance:
                # Simulate timeout after accepting the request internally
                return ExecutionReceipt(
                    transaction_id=request.transaction_id,
                    provider_transaction_id=None,
                    status="UNKNOWN",
                    timestamp=now,
                    error_message="Provider network timeout after request accepted"
                )

            return ExecutionReceipt(
                transaction_id=request.transaction_id,
                provider_transaction_id=record["payment_id"],
                status=outcome,
                timestamp=now,
                error_message=error_message
            )

    async def get_payment_status(self, idempotency_key: str) -> Optional[ExecutionReceipt]:
        async with self._lock:
            if idempotency_key not in self._store:
                return None
            existing = self._store[idempotency_key]
            return ExecutionReceipt(
                transaction_id=existing["transaction_id"],
                provider_transaction_id=existing["payment_id"],
                status=existing["status"],
                timestamp=existing["created_at"],
                error_message=existing.get("error_message")
            )
