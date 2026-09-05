with open("app/domain/models.py", "r") as f:
    content = f.read()

content = content.replace(
    "investigation: Optional[Dict[str, Any]] = None",
    "investigation: Optional[Dict[str, Any]] = None\n    evidence: Optional[Dict[str, Any]] = None\n    explanation: Optional[Dict[str, Any]] = None\n    policy_metadata: Optional[Dict[str, str]] = None"
)

content = content.replace(
    "current_hash: Optional[str] = None\n\n    timestamp: datetime",
    "current_hash: Optional[str] = None\n\n    evidence: Optional[Dict[str, Any]] = None\n    explanation: Optional[Dict[str, Any]] = None\n\n    timestamp: datetime"
)

with open("app/domain/models.py", "w") as f:
    f.write(content)
