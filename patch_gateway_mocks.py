with open("app/domain/gateway.py", "r") as f:
    content = f.read()

content = content.replace("intent_hash=open_mandate.intent_hash", "intent_hash=str(open_mandate.intent_hash)")
content = content.replace("intent_hash=open_mandate.intent_hash", "intent_hash=str(open_mandate.intent_hash)") # For both intent and cryptographic
content = content.replace("cart_hash=closed_mandate.cart_hash", "cart_hash=str(closed_mandate.cart_hash)")
content = content.replace("actual_cart_hash=actual_cart_hash", "actual_cart_hash=str(actual_cart_hash)")
content = content.replace("idempotency_key=reservation_key", "idempotency_key=str(reservation_key)")
content = content.replace("semantic_result=sem_result.status", "semantic_result=str(sem_result.status)")
content = content.replace("confidence=sem_result.confidence", "confidence=float(sem_result.confidence)")
content = content.replace("policy_decision=\"ALLOW\" if decision.allowed else \"DENY\"", "policy_decision=str(\"ALLOW\" if decision.allowed else \"DENY\")")

with open("app/domain/gateway.py", "w") as f:
    f.write(content)
