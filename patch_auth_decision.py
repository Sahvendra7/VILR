with open("app/domain/models.py", "r") as f:
    content = f.read()

content = content.replace(
    "class AuthorizationDecision(BaseModel):\n    allowed: bool\n    violations: List[Dict[str, str]]\n    policy_version: str",
    "class AuthorizationDecision(BaseModel):\n    allowed: bool\n    violations: List[Dict[str, str]]\n    policy_version: str\n    policy_hash: str = \"\""
)

with open("app/domain/models.py", "w") as f:
    f.write(content)
