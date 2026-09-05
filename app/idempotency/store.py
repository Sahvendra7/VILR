import json
import structlog
from datetime import datetime, timezone
from typing import Tuple, Optional
import redis.asyncio as redis
from app.domain.interfaces import IdempotencyStore
from app.domain.errors import IdempotencyUnavailable, IdempotencyOwnershipFailure

logger = structlog.get_logger(__name__)

LUA_COMMIT = """
local key = KEYS[1]
local tx_id = ARGV[1]
local commit_ttl = ARGV[2]
local current = redis.call("GET", key)
if not current then return "NOT_FOUND" end
local data = cjson.decode(current)
if data.transaction_id ~= tx_id then return "OWNERSHIP_FAILURE" end
if data.status == "committed" then return "ALREADY_COMMITTED" end
if data.status ~= "reserved" then return "INVALID_STATE" end
data.status = "committed"
redis.call("SET", key, cjson.encode(data), "EX", commit_ttl)
return "OK"
"""

LUA_CONSUME_EXEC_TOKEN = """
local key = KEYS[1]
local tx_id = ARGV[1]
local expected_amount = ARGV[2]
local expected_currency = ARGV[3]
local expected_merchant = ARGV[4]
local expected_hash = ARGV[5]

local current = redis.call("GET", key)
if not current then return "NOT_FOUND" end
local data = cjson.decode(current)
if data.transaction_id ~= tx_id then return "OWNERSHIP_FAILURE" end
if data.status == "consumed" then return "ALREADY_CONSUMED" end
if data.status ~= "available" then return "INVALID_STATE" end

if tostring(data.auth_data.amount) ~= expected_amount then return "PARAM_MISMATCH" end
if data.auth_data.currency ~= expected_currency then return "PARAM_MISMATCH" end
if data.auth_data.merchant_id ~= expected_merchant then return "PARAM_MISMATCH" end
if data.auth_data.mandate_hash ~= expected_hash then return "PARAM_MISMATCH" end

data.status = "consumed"
redis.call("SET", key, cjson.encode(data), "KEEPTTL")
return cjson.encode(data.auth_data)
"""

LUA_RELEASE = """
local key = KEYS[1]
local tx_id = ARGV[1]
local current = redis.call("GET", key)
if not current then return "NOT_FOUND" end
local data = cjson.decode(current)
if data.transaction_id ~= tx_id then return "OWNERSHIP_FAILURE" end
if data.status == "committed" then return "CANNOT_RELEASE_COMMITTED" end
redis.call("DEL", key)
return "OK"
"""

def build_idempotency_key(open_mandate_hash: str, checkout_hash: str) -> str:
    """Builds the canonical VILR idempotency composite key."""
    return f"vilr:idempotency:{open_mandate_hash}:{checkout_hash}"

class RedisIdempotencyStore(IdempotencyStore):
    def __init__(self, redis_client: redis.Redis, committed_ttl: int = 86400):
        self.client = redis_client
        self._commit_script = self.client.register_script(LUA_COMMIT)
        self._release_script = self.client.register_script(LUA_RELEASE)
        self._consume_script = self.client.register_script(LUA_CONSUME_EXEC_TOKEN)
        self.committed_ttl = committed_ttl

    async def try_reserve(self, key: str, transaction_id: str, ttl_seconds: int = 300) -> bool:
        logger.info("RESERVATION_ATTEMPT", key=key, transaction_id=transaction_id)
        try:
            now = datetime.now(timezone.utc).isoformat()
            val = json.dumps({
                "transaction_id": transaction_id,
                "status": "reserved",
                "created_at": now
            })
            acquired = await self.client.set(key, val, ex=ttl_seconds, nx=True)
            if acquired:
                logger.info("RESERVATION_ACQUIRED", key=key, transaction_id=transaction_id)
                return True
            else:
                logger.info("RESERVATION_ALREADY_EXISTS", key=key, transaction_id=transaction_id)
                return False
        except redis.RedisError as e:
            logger.error("REDIS_UNAVAILABLE", error=str(e), key=key)
            raise IdempotencyUnavailable("Idempotency store is unavailable") from e

    async def commit(self, key: str, transaction_id: str) -> None:
        try:
            result = await self._commit_script(keys=[key], args=[transaction_id, self.committed_ttl])
            result_str = result.decode("utf-8") if isinstance(result, bytes) else result

            if result_str == "OK" or result_str == "ALREADY_COMMITTED":
                logger.info("RESERVATION_COMMITTED", key=key, transaction_id=transaction_id)
            elif result_str == "INVALID_STATE":
                raise ValueError("Cannot commit a reservation that is not in reserved state")
            elif result_str == "NOT_FOUND":
                logger.warning("RESERVATION_EXPIRED", key=key, transaction_id=transaction_id, op="commit")
                raise ValueError("Reservation not found or expired")
            elif result_str == "OWNERSHIP_FAILURE":
                logger.warning("RESERVATION_OWNERSHIP_FAILURE", key=key, transaction_id=transaction_id, op="commit")
                raise IdempotencyOwnershipFailure("Cannot commit a reservation owned by another transaction")
            else:
                raise ValueError(f"Unexpected commit result: {result_str}")
        except redis.RedisError as e:
            logger.error("REDIS_UNAVAILABLE", error=str(e), key=key)
            raise IdempotencyUnavailable("Idempotency store is unavailable") from e

    async def release(self, key: str, transaction_id: str) -> None:
        try:
            result = await self._release_script(keys=[key], args=[transaction_id])
            result_str = result.decode("utf-8") if isinstance(result, bytes) else result

            if result_str == "OK" or result_str == "ALREADY_COMMITTED":
                logger.info("RESERVATION_RELEASED", key=key, transaction_id=transaction_id)
            elif result_str == "INVALID_STATE":
                raise ValueError("Cannot commit a reservation that is not in reserved state")
            elif result_str == "NOT_FOUND":
                # Safe response / no-op
                pass
            elif result_str == "OWNERSHIP_FAILURE":
                logger.warning("RESERVATION_OWNERSHIP_FAILURE", key=key, transaction_id=transaction_id, op="release")
                raise IdempotencyOwnershipFailure("Cannot release a reservation owned by another transaction")
            elif result_str == "CANNOT_RELEASE_COMMITTED":
                logger.warning("RESERVATION_RELEASE_FAILED", key=key, reason="already committed")
                raise ValueError("Cannot release a committed reservation")
        except redis.RedisError as e:
            logger.error("REDIS_UNAVAILABLE", error=str(e), key=key)
            raise IdempotencyUnavailable("Idempotency store is unavailable") from e

    async def is_reserved_or_committed(self, key: str) -> Tuple[bool, Optional[str]]:
        try:
            val = await self.client.get(key)
            if not val:
                return False, None
            try:
                data = json.loads(val)
                return True, data.get("status")
            except json.JSONDecodeError:
                logger.error("RESERVATION_MALFORMED", key=key)
                return True, "unknown"
        except redis.RedisError as e:
            logger.error("REDIS_UNAVAILABLE", error=str(e), key=key)
            raise IdempotencyUnavailable("Idempotency store is unavailable") from e

    async def create_execution_token(self, token: str, transaction_id: str, auth_data: dict, ttl_seconds: int = 3600) -> None:
        key = f"vilr:exec_token:{token}"
        val = json.dumps({
            "transaction_id": transaction_id,
            "status": "available",
            "auth_data": auth_data
        })
        success = await self.client.set(key, val, ex=ttl_seconds, nx=True)
        if not success:
            raise ValueError("Token collision or already exists")

    async def consume_execution_token(self, token: str, transaction_id: str, expected_amount: str, expected_currency: str, expected_merchant: str, expected_hash: str) -> dict:
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

        return json.loads(result_str)
