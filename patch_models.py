import re

with open("app/domain/models.py", "r") as f:
    content = f.read()

# Add mandate_hash to ExecutionRequest
new_execution_request = """class ExecutionRequest(BaseModel):
    transaction_id: Identifier
    idempotency_key: Identifier
    merchant_id: Identifier
    amount: Money
    currency: CurrencyCode
    payment_method_id: Identifier
    mandate_hash: str"""

content = re.sub(r"class ExecutionRequest\(BaseModel\):.*?payment_method_id: Identifier", new_execution_request, content, flags=re.DOTALL)

with open("app/domain/models.py", "w") as f:
    f.write(content)
