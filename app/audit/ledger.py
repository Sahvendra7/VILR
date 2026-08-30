import hashlib
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.models import AuditRecord
from app.domain.interfaces import AuditLedger

GENESIS_HASH = "0" * 64

class MemoryAuditLedger(AuditLedger):
    def __init__(self):
        # transaction_id -> List[AuditRecord]
        self._store: Dict[str, List[AuditRecord]] = {}

    def _canonicalize(self, record_dict: dict) -> str:
        d = dict(record_dict)
        d.pop("record_hash", None)
        # Ensure all types are json serializable by relying on Pydantic if needed
        # We'll just cast datetime if it's there
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat().replace("+00:00", "Z")
        return json.dumps(d, separators=(',', ':'), sort_keys=True)

    def _hash(self, canonical_str: str) -> str:
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

    async def record(self, record: AuditRecord) -> None:
        tx_id = record.transaction_id
        if tx_id not in self._store:
            self._store[tx_id] = []
        self._store[tx_id].append(record)

    async def get(self, transaction_id: str) -> Optional[AuditRecord]:
        if transaction_id not in self._store or not self._store[transaction_id]:
            return None
        return self._store[transaction_id][-1]

    async def list_by_transaction(self, transaction_id: str) -> List[AuditRecord]:
        return self._store.get(transaction_id, [])

    async def list_by_user(self, user_id: str) -> List[AuditRecord]:
        results = []
        for records in self._store.values():
            if records and records[0].user_id == user_id:
                results.extend(records)
        return results

    async def verify_chain(self, transaction_id: str) -> dict:
        records = self._store.get(transaction_id, [])
        if not records:
            return {"valid": False, "broken_at": 0, "reason": "NO_RECORDS"}

        expected_prev = GENESIS_HASH
        for i, rec in enumerate(records):
            if rec.prev_record_hash != expected_prev:
                return {"valid": False, "broken_at": i, "reason": "PREV_HASH_MISMATCH"}
            
            canonical = self._canonicalize(rec.model_dump(mode='json'))
            computed_hash = self._hash(canonical)
            if computed_hash != rec.record_hash:
                return {"valid": False, "broken_at": i, "reason": "RECORD_HASH_MISMATCH"}
            
            expected_prev = computed_hash

        return {"valid": True, "records_checked": len(records), "broken_at": None}

    def build_record(self, base_data: dict) -> AuditRecord:
        # First build to trigger Pydantic defaults and type coercion
        base_data["record_hash"] = "temp"
        rec = AuditRecord(**base_data)
        canonical = self._canonicalize(rec.model_dump(mode='json'))
        record_hash = self._hash(canonical)
        rec.record_hash = record_hash
        return rec
