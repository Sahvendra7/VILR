import re

with open("app/idempotency/store.py", "r") as f:
    content = f.read()

# Update Lua script
new_lua = """LUA_CONSUME_EXEC_TOKEN = \"\"\"
local key = KEYS[1]
local tx_id = ARGV[1]
local expected_amount = tonumber(ARGV[2])
local expected_currency = ARGV[3]
local expected_merchant = ARGV[4]
local expected_hash = ARGV[5]

local current = redis.call("GET", key)
if not current then return "NOT_FOUND" end
local data = cjson.decode(current)
if data.transaction_id ~= tx_id then return "OWNERSHIP_FAILURE" end
if data.status == "consumed" then return "ALREADY_CONSUMED" end
if data.status ~= "available" then return "INVALID_STATE" end

if tonumber(data.auth_data.amount) ~= expected_amount then return "PARAM_MISMATCH" end
if data.auth_data.currency ~= expected_currency then return "PARAM_MISMATCH" end
if data.auth_data.merchant_id ~= expected_merchant then return "PARAM_MISMATCH" end
if data.auth_data.mandate_hash ~= expected_hash then return "PARAM_MISMATCH" end

data.status = "consumed"
redis.call("SET", key, cjson.encode(data), "KEEPTTL")
return cjson.encode(data.auth_data)
\"\"\""""

content = re.sub(r'LUA_CONSUME_EXEC_TOKEN = \"\"\".*?\"\"\"', new_lua, content, flags=re.DOTALL)

# Update consume_execution_token method signature and call
old_method = """    async def consume_execution_token(self, token: str, transaction_id: str) -> dict:
        key = f"vilr:exec_token:{token}"
        result = await self._consume_script(keys=[key], args=[transaction_id])
        result_str = result.decode("utf-8") if isinstance(result, bytes) else result
        
        if result_str == "NOT_FOUND":
            raise ValueError("Invalid or expired execution token")
        elif result_str == "OWNERSHIP_FAILURE":
            from app.domain.errors import InvalidRequest
            raise InvalidRequest("Token transaction mismatch")
        elif result_str == "ALREADY_CONSUMED":
            from app.domain.errors import DuplicateExecution
            raise DuplicateExecution("Execution token already consumed")
        elif result_str == "INVALID_STATE":
            raise ValueError("Invalid token state")
            
        return json.loads(result_str)"""

new_method = """    async def consume_execution_token(self, token: str, transaction_id: str, expected_amount: float, expected_currency: str, expected_merchant: str, expected_hash: str) -> dict:
        key = f"vilr:exec_token:{token}"
        result = await self._consume_script(keys=[key], args=[transaction_id, str(expected_amount), expected_currency, expected_merchant, expected_hash])
        result_str = result.decode("utf-8") if isinstance(result, bytes) else result
        
        if result_str == "NOT_FOUND":
            raise ValueError("Invalid or expired execution token")
        elif result_str == "OWNERSHIP_FAILURE":
            from app.domain.errors import InvalidRequest
            raise InvalidRequest("Token transaction mismatch")
        elif result_str == "ALREADY_CONSUMED":
            from app.domain.errors import DuplicateExecution
            raise DuplicateExecution("Execution token already consumed")
        elif result_str == "PARAM_MISMATCH":
            from app.domain.errors import InvalidRequest
            raise InvalidRequest("Execution parameters do not match authorized context")
        elif result_str == "INVALID_STATE":
            raise ValueError("Invalid token state")
            
        return json.loads(result_str)"""

content = content.replace(old_method, new_method)

with open("app/idempotency/store.py", "w") as f:
    f.write(content)

# Now update app/domain/gateway.py
with open("app/domain/gateway.py", "r") as f:
    gateway_content = f.read()

old_execute = """    async def execute(self, request: GatewayExecuteRequest) -> dict:
        tx_id = request.transaction_id
        
        try:
            auth_data = await self.idempotency.consume_execution_token(request.execution_token, tx_id)
        except ValueError as e:
            raise InvalidRequest(str(e))
            
        if (float(auth_data["amount"]) != float(request.amount) or
            auth_data["currency"] != request.currency or
            auth_data["merchant_id"] != request.merchant_id or
            auth_data["mandate_hash"] != request.mandate_hash):
            raise InvalidRequest("Execution parameters do not match authorized context")"""

new_execute = """    async def execute(self, request: GatewayExecuteRequest) -> dict:
        tx_id = request.transaction_id
        
        try:
            auth_data = await self.idempotency.consume_execution_token(
                request.execution_token, tx_id, 
                float(request.amount), request.currency, request.merchant_id, request.mandate_hash
            )
        except ValueError as e:
            raise InvalidRequest(str(e))"""

gateway_content = gateway_content.replace(old_execute, new_execute)

with open("app/domain/gateway.py", "w") as f:
    f.write(gateway_content)
