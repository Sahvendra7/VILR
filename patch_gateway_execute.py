import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

replacement = """        try:
            receipt = await self.payment_executor.execute(exec_request, state)
            context["execution_status"] = receipt.status
            
            # Retrieve prior record to update evidence
            prior_record = await self.audit.get(tx_id)
            if prior_record and prior_record.evidence:
                ev = prior_record.evidence.copy()
                if "execution" in ev:
                    ev["execution"]["execution_status"] = receipt.status
                    ev["execution"]["provider_request_id"] = receipt.provider_transaction_id or request.provider_idempotency_key
                context["evidence"] = ev
                
            await self._log(tx_id, state.current_state, **context)
            
            return {"""

content = re.sub(r'        try:\n            receipt = await self.payment_executor.execute\(exec_request, state\)\n            context\["execution_status"\] = receipt.status\n            await self._log\(tx_id, state.current_state, \*\*context\)\n            \n            return \{', replacement, content)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
