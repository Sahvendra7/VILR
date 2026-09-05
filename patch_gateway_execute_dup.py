import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

replacement = """        try:
            auth_data = await self.idempotency.consume_execution_token(
                request.execution_token, tx_id, 
                str(request.amount), request.currency, request.merchant_id, request.mandate_hash
            )
        except DuplicateExecution as e:
            # Token already consumed -> execution replay
            state = self._tx_states.get(tx_id)
            if state:
                state.transition_to(TransactionState.REPLAY_DETECTED)
                context_replay = {
                    "merchant_id": request.merchant_id,
                    "payment_attempt_id": request.provider_idempotency_key,
                    "failure_reason": "Execution token already consumed",
                    "evidence": {
                        "replay": {
                            "idempotency_key": request.execution_token,
                            "replay_detected": True,
                            "reservation_status": "COMMITTED",
                            "execution_token_status": "ALREADY_CONSUMED"
                        }
                    }
                }
                await self._log(tx_id, TransactionState.REPLAY_DETECTED, **context_replay)
            raise
        except ValueError as e:"""

content = re.sub(r'        try:\n            auth_data = await self.idempotency.consume_execution_token\(\n                request.execution_token, tx_id, \n                str\(request.amount\), request.currency, request.merchant_id, request.mandate_hash\n            \)\n        except ValueError as e:', replacement, content)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
