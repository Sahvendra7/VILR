import pytest
from datetime import datetime, UTC
from uuid import uuid4

from app.audit.ledger import MemoryAuditLedger, GENESIS_HASH

@pytest.fixture
def ledger():
    return MemoryAuditLedger()

def make_base_record(tx_id="tx_123"):
    return {
        "transaction_id": tx_id,
        "user_id": "usr_1",
        "agent_id": "agt_1",
        "merchant_id": "mer_1",
        "intent_hash": "inh_1",
        "open_mandate_hash": "omh_1",
        "cart_hash": "ch_1",
        "state": "INTENT_RECEIVED",
        "timestamp": datetime.now(UTC),
        "nonce": uuid4().hex
    }

@pytest.mark.asyncio
async def test_a_01_first_audit_record_uses_genesis_hash(ledger):
    data = make_base_record()
    data["prev_record_hash"] = GENESIS_HASH
    rec = ledger.build_record(data)
    await ledger.record(rec)

    assert rec.prev_record_hash == GENESIS_HASH

@pytest.mark.asyncio
async def test_a_02_sequential_records_form_valid_chain(ledger):
    tx_id = "tx_seq"

    r1_data = make_base_record(tx_id)
    r1_data["prev_record_hash"] = GENESIS_HASH
    r1 = ledger.build_record(r1_data)
    await ledger.record(r1)

    r2_data = make_base_record(tx_id)
    r2_data["state"] = "AP2_VERIFIED"
    r2_data["prev_record_hash"] = r1.record_hash
    r2 = ledger.build_record(r2_data)
    await ledger.record(r2)

    res = await ledger.verify_chain(tx_id)
    assert res["valid"] is True
    assert res["records_checked"] == 2

@pytest.mark.asyncio
async def test_a_03_modified_record_is_detected(ledger):
    tx_id = "tx_mod"
    r1_data = make_base_record(tx_id)
    r1_data["prev_record_hash"] = GENESIS_HASH
    r1 = ledger.build_record(r1_data)
    await ledger.record(r1)

    # Tamper
    r1.state = "HACKED"

    res = await ledger.verify_chain(tx_id)
    assert res["valid"] is False
    assert res["reason"] == "RECORD_HASH_MISMATCH"

@pytest.mark.asyncio
async def test_a_04_deleted_record_is_detected(ledger):
    tx_id = "tx_del"
    r1_data = make_base_record(tx_id)
    r1_data["prev_record_hash"] = GENESIS_HASH
    r1 = ledger.build_record(r1_data)

    r2_data = make_base_record(tx_id)
    r2_data["state"] = "AP2_VERIFIED"
    r2_data["prev_record_hash"] = r1.record_hash
    r2 = ledger.build_record(r2_data)

    await ledger.record(r1)
    await ledger.record(r2)

    # Delete r1
    ledger._store[tx_id].pop(0)

    res = await ledger.verify_chain(tx_id)
    assert res["valid"] is False
    assert res["reason"] == "PREV_HASH_MISMATCH" # Genesis not matched

@pytest.mark.asyncio
async def test_a_05_reordered_record_is_detected(ledger):
    tx_id = "tx_reord"
    r1_data = make_base_record(tx_id)
    r1_data["prev_record_hash"] = GENESIS_HASH
    r1 = ledger.build_record(r1_data)

    r2_data = make_base_record(tx_id)
    r2_data["state"] = "AP2_VERIFIED"
    r2_data["prev_record_hash"] = r1.record_hash
    r2 = ledger.build_record(r2_data)

    # Store out of order
    await ledger.record(r2)
    await ledger.record(r1)

    res = await ledger.verify_chain(tx_id)
    assert res["valid"] is False
    assert res["reason"] == "PREV_HASH_MISMATCH"

@pytest.mark.asyncio
async def test_a_06_modified_previous_hash_is_detected(ledger):
    tx_id = "tx_mod_prev"
    r1_data = make_base_record(tx_id)
    r1_data["prev_record_hash"] = GENESIS_HASH
    r1 = ledger.build_record(r1_data)

    r2_data = make_base_record(tx_id)
    r2_data["state"] = "AP2_VERIFIED"
    r2_data["prev_record_hash"] = "fake_hash" # Tampered before signing
    r2 = ledger.build_record(r2_data)

    await ledger.record(r1)
    await ledger.record(r2)

    res = await ledger.verify_chain(tx_id)
    assert res["valid"] is False
    assert res["reason"] == "PREV_HASH_MISMATCH"

@pytest.mark.asyncio
async def test_a_07_different_transaction_chains_remain_independent(ledger):
    tx1 = "tx_1"
    tx2 = "tx_2"

    r1_data = make_base_record(tx1)
    r1_data["prev_record_hash"] = GENESIS_HASH
    r1 = ledger.build_record(r1_data)
    await ledger.record(r1)

    r2_data = make_base_record(tx2)
    r2_data["prev_record_hash"] = GENESIS_HASH
    r2 = ledger.build_record(r2_data)
    await ledger.record(r2)

    res1 = await ledger.verify_chain(tx1)
    res2 = await ledger.verify_chain(tx2)

    assert res1["valid"] is True
    assert res2["valid"] is True

@pytest.mark.asyncio
async def test_a_08_audit_retrieval_preserves_ordering(ledger):
    tx_id = "tx_ord"
    r1 = ledger.build_record({**make_base_record(tx_id), "prev_record_hash": GENESIS_HASH, "state": "INTENT_RECEIVED"})
    r2 = ledger.build_record({**make_base_record(tx_id), "prev_record_hash": r1.record_hash, "state": "AP2_VERIFIED"})
    r3 = ledger.build_record({**make_base_record(tx_id), "prev_record_hash": r2.record_hash, "state": "CART_VERIFIED"})

    await ledger.record(r1)
    await ledger.record(r2)
    await ledger.record(r3)

    records = await ledger.list_by_transaction(tx_id)
    assert [r.state for r in records] == ["INTENT_RECEIVED", "AP2_VERIFIED", "CART_VERIFIED"]

@pytest.mark.asyncio
async def test_a_09_authorization_failure_creates_evidence(ledger):
    tx_id = "tx_fail"
    r1 = ledger.build_record({**make_base_record(tx_id), "prev_record_hash": GENESIS_HASH, "state": "POLICY_DENIED"})
    await ledger.record(r1)

    records = await ledger.list_by_transaction(tx_id)
    assert records[0].state == "POLICY_DENIED"

@pytest.mark.asyncio
async def test_a_10_payment_unknown_creates_evidence(ledger):
    tx_id = "tx_unk"
    r1 = ledger.build_record({**make_base_record(tx_id), "prev_record_hash": GENESIS_HASH, "state": "PAYMENT_UNKNOWN"})
    await ledger.record(r1)

    records = await ledger.list_by_transaction(tx_id)
    assert records[0].state == "PAYMENT_UNKNOWN"

@pytest.mark.asyncio
async def test_a_11_unknown_reconciliation_updates_evidence(ledger):
    tx_id = "tx_recon"
    r1 = ledger.build_record({**make_base_record(tx_id), "prev_record_hash": GENESIS_HASH, "state": "PAYMENT_UNKNOWN"})
    await ledger.record(r1)

    r2 = ledger.build_record({**make_base_record(tx_id), "prev_record_hash": r1.record_hash, "state": "PAYMENT_CONFIRMED"})
    await ledger.record(r2)

    records = await ledger.list_by_transaction(tx_id)
    assert records[-1].state == "PAYMENT_CONFIRMED"

@pytest.mark.asyncio
async def test_a_12_sensitive_data_is_not_persisted(ledger):
    tx_id = "tx_sens"
    # The record schema simply lacks fields for private keys or raw APIs
    # We test that an attempt to include them in build_record does not serialize them into the model
    data = make_base_record(tx_id)
    data["prev_record_hash"] = GENESIS_HASH
    data["private_key"] = "SUPER_SECRET"

    r1 = ledger.build_record(data)
    await ledger.record(r1)

    # Pydantic strips extra fields by default or raises. Assuming it strips or they aren't part of the dump.
    dump = r1.model_dump()
    assert "private_key" not in dump
