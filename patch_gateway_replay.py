import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

replacement = """        reserved = await self.idempotency.try_reserve(reservation_key, tx_id, 300)
        if not reserved:
            state.transition_to(TransactionState.REPLAY_DETECTED)
            context["failure_reason"] = "Replay detected"
            
            # Construct partial evidence for replay
            context["evidence"] = {
                "replay": {
                    "idempotency_key": str(reservation_key),
                    "replay_detected": True,
                    "reservation_status": "CONFLICT",
                    "execution_token_status": "NONE"
                }
            }
            
            await self._log(tx_id, TransactionState.REPLAY_DETECTED, **context)
            raise ReplayDetected("Duplicate reservation")"""

content = re.sub(r'        reserved = await self.idempotency.try_reserve\(reservation_key, tx_id, 300\)\n        if not reserved:\n            state.transition_to\(TransactionState.REPLAY_DETECTED\)\n            context\["failure_reason"\] = "Replay detected"\n            await self._log\(tx_id, TransactionState.REPLAY_DETECTED, \*\*context\)\n            raise ReplayDetected\("Duplicate reservation"\)', replacement, content)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
