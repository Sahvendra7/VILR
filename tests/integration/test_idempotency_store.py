import pytest
import pytest_asyncio
import asyncio
import uuid
import redis.asyncio as redis
from app.idempotency.store import RedisIdempotencyStore, build_idempotency_key
from app.domain.errors import IdempotencyOwnershipFailure, IdempotencyUnavailable

@pytest_asyncio.fixture
async def redis_client():
    client = redis.Redis(host='localhost', port=6379, db=0)
    await client.ping()
    yield client
    await client.flushdb()
    await client.aclose()

@pytest_asyncio.fixture
def store(redis_client):
    return RedisIdempotencyStore(redis_client, committed_ttl=10)

def gen_key():
    return build_idempotency_key(uuid.uuid4().hex, uuid.uuid4().hex)

@pytest.mark.asyncio
async def test_reserve_success(store):
    key = gen_key()
    assert await store.try_reserve(key, "tx_1") == True
    
    # ID-10: Wrong transaction cannot release
    with pytest.raises(IdempotencyOwnershipFailure):
        await store.release(key, "tx_wrong")
        
    # Owner can release
    await store.release(key, "tx_1")
    
    # Can reserve again
    assert await store.try_reserve(key, "tx_2") == True

@pytest.mark.asyncio
async def test_reserve_semantic_failure_release(store):
    # ID-07: Reserve -> semantic failure -> release -> retry succeeds
    key = gen_key()
    assert await store.try_reserve(key, "tx_1") == True
    # Simulate semantic failure by releasing
    await store.release(key, "tx_1")
    # Retry succeeds
    assert await store.try_reserve(key, "tx_2") == True

@pytest.mark.asyncio
async def test_reserve_policy_denial_release(store):
    # ID-08: Reserve -> policy denial -> release -> retry succeeds
    key = gen_key()
    assert await store.try_reserve(key, "tx_1") == True
    await store.release(key, "tx_1")
    assert await store.try_reserve(key, "tx_2") == True

@pytest.mark.asyncio
async def test_reserve_commit(store):
    # ID-09: Reserve -> commit -> subsequent attempt rejected
    key = gen_key()
    assert await store.try_reserve(key, "tx_1") == True
    await store.commit(key, "tx_1")
    assert await store.try_reserve(key, "tx_2") == False

@pytest.mark.asyncio
async def test_wrong_tx_cannot_commit(store):
    # ID-11
    key = gen_key()
    await store.try_reserve(key, "tx_1")
    with pytest.raises(IdempotencyOwnershipFailure):
        await store.commit(key, "tx_wrong")

@pytest.mark.asyncio
async def test_committed_cannot_be_released(store):
    # ID-12
    key = gen_key()
    await store.try_reserve(key, "tx_1")
    await store.commit(key, "tx_1")
    with pytest.raises(ValueError, match="Cannot release a committed reservation"):
        await store.release(key, "tx_1")

@pytest.mark.asyncio
async def test_tentative_expiry(store):
    # ID-13
    key = gen_key()
    # reserve with 1 sec ttl
    assert await store.try_reserve(key, "tx_1", ttl_seconds=1) == True
    assert await store.try_reserve(key, "tx_2") == False
    await asyncio.sleep(1.1)
    # Expired, should succeed now
    assert await store.try_reserve(key, "tx_3") == True

@pytest.mark.asyncio
async def test_same_mandate_different_checkouts(store):
    # ID-14
    m_hash = "mandate_1"
    key1 = build_idempotency_key(m_hash, "checkout_A")
    key2 = build_idempotency_key(m_hash, "checkout_B")
    
    assert await store.try_reserve(key1, "tx_1") == True
    assert await store.try_reserve(key2, "tx_2") == True

@pytest.mark.asyncio
async def test_concurrent_same_checkout(store):
    # ID-15 & Attack A & ID-18/19 style race
    key = gen_key()
    
    async def worker(i):
        return await store.try_reserve(key, f"tx_{i}")
        
    results = await asyncio.gather(*(worker(i) for i in range(50)))
    
    # Exactly one winner
    assert results.count(True) == 1
    assert results.count(False) == 49

@pytest.mark.asyncio
async def test_redis_unavailable():
    # ID-16 & Attack H
    # Point to a wrong port
    bad_client = redis.Redis(host='localhost', port=9999, socket_connect_timeout=0.1)
    bad_store = RedisIdempotencyStore(bad_client)
    
    with pytest.raises(IdempotencyUnavailable):
        await bad_store.try_reserve(gen_key(), "tx_1")

@pytest.mark.asyncio
async def test_malformed_reservation(store, redis_client):
    # ID-17
    key = gen_key()
    await redis_client.set(key, "not_json")
    
    is_reserved, status = await store.is_reserved_or_committed(key)
    assert is_reserved == True
    assert status == "unknown"

@pytest.mark.asyncio
async def test_transaction_id_collision_different_keys(store):
    # ID-20
    key1 = build_idempotency_key("m1", "c1")
    key2 = build_idempotency_key("m1", "c2")
    
    assert await store.try_reserve(key1, "tx_duplicate") == True
    assert await store.try_reserve(key2, "tx_duplicate") == True

@pytest.mark.asyncio
async def test_is_reserved_or_committed(store):
    key = gen_key()
    res, stat = await store.is_reserved_or_committed(key)
    assert res == False
    
    await store.try_reserve(key, "tx_1")
    res, stat = await store.is_reserved_or_committed(key)
    assert res == True
    assert stat == "reserved"
    
    await store.commit(key, "tx_1")
    res, stat = await store.is_reserved_or_committed(key)
    assert res == True
    assert stat == "committed"

@pytest.mark.asyncio
async def test_idempotent_commit(store):
    key = gen_key()
    await store.try_reserve(key, "tx_1")
    await store.commit(key, "tx_1")
    # Calling commit again on already committed reservation by the same owner should succeed (idempotent)
    await store.commit(key, "tx_1")
    res, stat = await store.is_reserved_or_committed(key)
    assert stat == "committed"


@pytest.mark.asyncio
async def test_release_not_found(store):
    # ID-x: Safe response when key is absent
    key = gen_key()
    await store.release(key, "tx_1") # Should not raise

@pytest.mark.asyncio
async def test_commit_not_found(store):
    key = gen_key()
    with pytest.raises(ValueError, match="Reservation not found or expired"):
        await store.commit(key, "tx_1")

@pytest.mark.asyncio
async def test_try_reserve_returns_false_if_owned_by_other(store):
    key = gen_key()
    assert await store.try_reserve(key, "tx_1") == True
    assert await store.try_reserve(key, "tx_2") == False

@pytest.mark.asyncio
async def test_try_reserve_returns_false_if_already_committed(store):
    key = gen_key()
    await store.try_reserve(key, "tx_1")
    await store.commit(key, "tx_1")
    assert await store.try_reserve(key, "tx_1") == False
    assert await store.try_reserve(key, "tx_2") == False

@pytest.mark.asyncio
async def test_commit_extends_ttl(store, redis_client):
    key = gen_key()
    await store.try_reserve(key, "tx_1", ttl_seconds=2)
    # Commit changes TTL to store.committed_ttl (10 in test)
    await store.commit(key, "tx_1")
    ttl = await redis_client.ttl(key)
    assert ttl > 2 and ttl <= 10

@pytest.mark.asyncio
async def test_commit_unknown_status(store, redis_client):
    key = gen_key()
    import json
    # manually set bad status
    await redis_client.set(key, json.dumps({"transaction_id": "tx_1", "status": "unknown"}))
    with pytest.raises(ValueError):
        await store.commit(key, "tx_1")

@pytest.mark.asyncio
async def test_release_unknown_status(store, redis_client):
    key = gen_key()
    import json
    await redis_client.set(key, json.dumps({"transaction_id": "tx_1", "status": "unknown"}))
    # the Lua script only explicitly blocks "committed". "unknown" should be deletable if owned
    await store.release(key, "tx_1")
    res, _ = await store.is_reserved_or_committed(key)
    assert res == False

