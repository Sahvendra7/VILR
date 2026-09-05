import re
with open("app/domain/gateway.py", "r") as f:
    content = f.read()

replacement = """        execution_status = record.execution_status or "NOT_REACHED"
        if record.state == "REPLAY_DETECTED":
            execution_status = "BLOCKED_REPLAY"
            
        provider_call = "NO" if execution_status in ["NOT_REACHED", "BLOCKED_REPLAY"] else "YES"
        
        provider_request_id = record.payment_attempt_id if hasattr(record, "payment_attempt_id") and record.payment_attempt_id else None
        
        automatic_retry = "NO" if execution_status == "UNKNOWN" else None
        reconciliation = "REQUIRED" if execution_status == "UNKNOWN" else None

        receipt = SecurityReceipt(
            receipt_id=f"rec_{transaction_id}",
            request_id=transaction_id,
            intent_id=record.intent_hash,
            transaction_id=transaction_id,
            intent_verified=record.intent_hash != "unknown",
            cryptographic_verification=record.cart_hash != "unknown",
            cart_verified=record.cart_hash != "unknown",
            replay_check="CLEAR" if record.state not in ["REPLAY_DETECTED"] else "FAILED",
            semantic_result=record.semantic_decision,
            policy_result=record.policy_decision or "NOT_REACHED",
            execution_result=execution_status,
            execution_status=execution_status,
            provider_call=provider_call,
            provider_request_id=provider_request_id,
            automatic_retry=automatic_retry,
            reconciliation=reconciliation,
            final_decision=record.authorization_status or ("DENIED" if record.execution_status != "SUCCESS" else "AUTHORIZED"),
            decision_source="SYSTEM",
            explanation_source="ExceptionIntelligence" if record.investigation else None,
            policy_version=record.explanation.get("policy_version", "1.0") if getattr(record, "explanation", None) else "1.0",
            evidence=record.evidence,
            explanation=record.explanation,
            audit_event_id=record.record_hash,
            previous_hash=record.prev_record_hash,
            current_hash=record.record_hash,
            timestamp=record.timestamp
        )"""

content = re.sub(r'        receipt = SecurityReceipt\(.*?timestamp=record.timestamp\n        \)', replacement, content, flags=re.DOTALL)

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
