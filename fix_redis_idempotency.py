with open("app/idempotency/store.py", "r") as f:
    content = f.read()

LUA_CONSUME = """
local key = KEYS[1]
local tx_id = ARGV[1]
local current = redis.call("GET", key)
if not current then return "NOT_FOUND" end
local data = cjson.decode(current)
if data.transaction_id ~= tx_id then return "OWNERSHIP_FAILURE" end
if data.status == "consumed" then return "ALREADY_CONSUMED" end
if data.status ~= "available" then return "INVALID_STATE" end
data.status = "consumed"
redis.call("SET", key, cjson.encode(data), "KEEPTTL")
return cjson.encode(data.auth_data)
"""

if "LUA_CONSUME_EXEC_TOKEN" not in content:
    content = content.replace('LUA_RELEASE = """', f'LUA_CONSUME_EXEC_TOKEN = """{LUA_CONSUME}"""\n\nLUA_RELEASE = """')
    
    methods = """
    async def create_execution_token(self, token: str, transaction_id: str, auth_data: dict, ttl_seconds: int = 3600) -> None:
        key = f"vilr:exec_token:{token}"
        val = json.dumps({
            "transaction_id": transaction_id,
            "status": "available",
            "auth_data": auth_data
        })
        await self.client.set(key, val, ex=ttl_seconds, nx=True)

    async def consume_execution_token(self, token: str, transaction_id: str) -> dict:
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
            
        return json.loads(result_str)
"""
    content = content.replace(
        "self._release_script = self.client.register_script(LUA_RELEASE)",
        "self._release_script = self.client.register_script(LUA_RELEASE)\n        self._consume_script = self.client.register_script(LUA_CONSUME_EXEC_TOKEN)"
    )
    content += methods

with open("app/idempotency/store.py", "w") as f:
    f.write(content)
