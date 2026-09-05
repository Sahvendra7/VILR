import re

with open("app/domain/models.py", "r") as f:
    content = f.read()

risk_models = """
class RiskFactor(BaseModel):
    signal: str
    weight: int
    description: str

class RiskAssessment(BaseModel):
    score: int
    level: str
    factors: List[RiskFactor] = Field(default_factory=list)
    calculated_at: datetime
"""

# Insert risk models before DecisionEvidence
content = content.replace("class DecisionEvidence(BaseModel):", risk_models + "\nclass DecisionEvidence(BaseModel):")

# Add risk to DecisionEvidence
content = content.replace("    execution: ExecutionEvidence", "    execution: ExecutionEvidence\n    risk: Optional[RiskAssessment] = None")

# Add risk to SecurityReceipt
content = content.replace("    explanation: Optional[Dict[str, Any]] = None", "    explanation: Optional[Dict[str, Any]] = None\n    risk: Optional[Dict[str, Any]] = None")

with open("app/domain/models.py", "w") as f:
    f.write(content)
