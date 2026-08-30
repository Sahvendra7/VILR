import re

with open("simulator/models.py", "r") as f:
    content = f.read()

# Replace ExecutionResult class definition
old_def = """class ExecutionResult:
    outcome: AttackOutcome
    http_status: int = 0
    error: str = ""
    payment_call_count: int = 0
    payment_creation_count: int = 0
    transaction_id: str = ""
    evidence: str = ""
"""
new_def = """class ExecutionResult:
    outcome: AttackOutcome
    http_status: int = 0
    error: str = ""
    payment_call_count: int = 0
    payment_creation_count: int = 0
    transaction_id: str = ""
    evidence: str = ""
"""
# well, wait, let's just do a regex replace from class ExecutionResult to @dataclass class AttackDefinition
import re
content = re.sub(r'class ExecutionResult:.*?@dataclass\nclass AttackDefinition:', 
                 '@dataclass\nclass ExecutionResult:\n    outcome: AttackOutcome\n    http_status: int = 0\n    error: str = ""\n    payment_call_count: int = 0\n    payment_creation_count: int = 0\n    transaction_id: str = ""\n    evidence: str = ""\n\n@dataclass\nclass AttackDefinition:', 
                 content, flags=re.DOTALL)

with open("simulator/models.py", "w") as f:
    f.write(content)

