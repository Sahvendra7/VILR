import json
import logging
from typing import Optional, List
from datetime import datetime
from supabase import create_client, Client
from app.domain.interfaces import AuditLedger
from app.domain.models import AuditRecord
from app.config.settings import settings
import hashlib

logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64

class SupabaseAuditLedger(AuditLedger):
    def __init__(self):
        url: str = settings.supabase_url
        key: str = settings.supabase_key
        self.client: Client = create_client(url, key)

    def _canonicalize(self, record_dict: dict) -> str:
        d = dict(record_dict)
        d.pop("record_hash", None)
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat().replace("+00:00", "Z")
        return json.dumps(d, separators=(',', ':'), sort_keys=True)

    def _hash(self, canonical_str: str) -> str:
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

    async def record(self, record: AuditRecord) -> None:
        try:
            data = {
                "transaction_id": record.transaction_id,
                "record": record.model_dump(mode='json')
            }
            # supabase-python uses synchronous calls under the hood here
            self.client.table("audit_ledger").insert(data).execute()
        except Exception as e:
            logger.error(f"SUPABASE_LEDGER_ERROR transaction_id={record.transaction_id} error={str(e)}")

    async def get(self, transaction_id: str) -> Optional[AuditRecord]:
        try:
            # Get latest record for transaction
            response = self.client.table("audit_ledger").select("*").eq("transaction_id", transaction_id).order("id", desc=True).limit(1).execute()
            if not response.data:
                return None
            
            return AuditRecord(**response.data[0]["record"])
        except Exception as e:
            logger.error(f"SUPABASE_GET_ERROR transaction_id={transaction_id} error={str(e)}")
            return None
            
    async def get_transaction_history(self, transaction_id: str) -> List[AuditRecord]:
        try:
            response = self.client.table("audit_ledger").select("*").eq("transaction_id", transaction_id).order("id").execute()
            return [AuditRecord(**row["record"]) for row in response.data]
        except Exception as e:
            logger.error(f"SUPABASE_HISTORY_ERROR transaction_id={transaction_id} error={str(e)}")
            return []
            
    def verify_chain(self, records: List[AuditRecord]) -> tuple[bool, str]:
        if not records:
            return False, "NO_RECORDS"

        expected_prev = GENESIS_HASH
        for i, rec in enumerate(records):
            if rec.prev_record_hash != expected_prev:
                return False, f"PREV_HASH_MISMATCH at pos {i}"
            
            canonical = self._canonicalize(rec.model_dump(mode='json'))
            computed_hash = self._hash(canonical)
            if computed_hash != rec.record_hash:
                return False, f"RECORD_HASH_MISMATCH at pos {i}"
            
            expected_prev = computed_hash

        return True, "Valid"
        
    def build_record(self, base_data: dict) -> AuditRecord:
        base_data["record_hash"] = "temp"
        rec = AuditRecord(**base_data)
        canonical = self._canonicalize(rec.model_dump(mode='json'))
        record_hash = self._hash(canonical)
        rec.record_hash = record_hash
        return rec
