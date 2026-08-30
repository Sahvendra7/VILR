import re

with open("app/domain/gateway.py", "r") as f:
    content = f.read()

# Remove _execution_tokens init
content = content.replace("        self._execution_tokens: Dict[str, dict] = {}\n", "")

# Replace authorize token creation
old_create = """
        execution_token = secrets.token_hex(32)
        self._execution_tokens[execution_token] = {
            "transaction_id": tx_id,
            "amount": request.cart.total_amount,
            "currency": request.cart.currency,
            "merchant_id": request.cart.merchant_id,
            "mandate_hash": closed_mandate.open_mandate_hash,
            "expires_at": datetime.now().timestamp() + 3600
        }

        return {
            "transaction_id": tx_id,
            "status": "AUTHORIZED",
            "execution_token": execution_token,
            "policy_version": decision.policy_version,
            "expires_at": datetime.fromtimestamp(self._execution_tokens[execution_token]["expires_at"]).isoformat()
        }
"""
new_create = """
        execution_token = secrets.token_hex(32)
        auth_data = {
            "amount": float(request.cart.total_amount),
            "currency": request.cart.currency,
            "merchant_id": request.cart.merchant_id,
            "mandate_hash": closed_mandate.open_mandate_hash
        }
        await self.idempotency.create_execution_token(execution_token, tx_id, auth_data, 3600)
        expires_at = datetime.now().timestamp() + 3600

        return {
            "transaction_id": tx_id,
            "status": "AUTHORIZED",
            "execution_token": execution_token,
            "policy_version": decision.policy_version,
            "expires_at": datetime.fromtimestamp(expires_at).isoformat()
        }
"""
content = content.replace(old_create.strip('\n'), new_create.strip('\n'))

# Replace execute token consumption
old_consume = """
        if request.execution_token not in self._execution_tokens:
            raise InvalidRequest("Invalid or expired execution token")
        
        auth_data = self._execution_tokens.pop(request.execution_token)
        
        if auth_data["transaction_id"] != tx_id:
            raise InvalidRequest("Token transaction mismatch")
        if datetime.now().timestamp() > auth_data["expires_at"]:
            raise InvalidRequest("Token expired")
"""
new_consume = """
        try:
            auth_data = await self.idempotency.consume_execution_token(request.execution_token, tx_id)
        except ValueError as e:
            raise InvalidRequest(str(e))
"""
content = content.replace(old_consume.strip('\n'), new_consume.strip('\n'))

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
