import re
with open("app/domain/models.py", "r") as f:
    content = f.read()

# Add fields to SecurityReceipt
new_fields = """
    execution_status: Optional[str] = None
    provider_call: Optional[str] = None
    provider_request_id: Optional[str] = None
    automatic_retry: Optional[str] = None
    reconciliation: Optional[str] = None
"""
content = content.replace("    execution_result: str\n", "    execution_result: str\n" + new_fields)

with open("app/domain/models.py", "w") as f:
    f.write(content)
