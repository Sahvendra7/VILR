from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Awaitable, Any

class AttackOutcome(str, Enum):
    BLOCKED = "BLOCKED"
    DETECTED = "DETECTED"
    NOT_BLOCKED = "NOT_BLOCKED"
    ERROR = "ERROR"
    INCONCLUSIVE = "INCONCLUSIVE"
    REGRESSION = "REGRESSION"
    ROBUSTNESS = "ROBUSTNESS"
    VALIDATION = "VALIDATION"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"

class DecisionOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"
    DETECTED = "DETECTED" # For audit tampering

class SideEffectOutcome(str, Enum):
    PAYMENT_EXECUTED = "PAYMENT_EXECUTED"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"

@dataclass
class ExecutionResult:
    actual_decision: DecisionOutcome
    actual_side_effect: SideEffectOutcome = SideEffectOutcome.UNKNOWN
    http_status: int = 0
    error: str = ""
    evidence: str = ""
    transaction_id: str = ""
    payment_call_count: int = 0
    payment_creation_count: int = 0
    outcome: Optional[AttackOutcome] = None # Legacy support

@dataclass
class AttackDefinition:
    attack_id: str
    name: str
    category: str
    description: str
    attacker: str
    preconditions: str
    malicious_input: str
    attack_path: str
    expected_decision: DecisionOutcome
    expected_side_effect: SideEffectOutcome
    expected_security_property: str
    expected_result: AttackOutcome # Legacy support
    defense_layer: str
    severity: Severity
    execute: Callable[['httpx.AsyncClient'], Awaitable[ExecutionResult]]

    @property
    def case_id(self): return self.attack_id

@dataclass
class EvaluationResult:
    case_id: str
    name: str
    category: str
    expected_decision: DecisionOutcome
    actual_decision: DecisionOutcome
    expected_side_effect: SideEffectOutcome
    actual_side_effect: SideEffectOutcome
    status: str # PASS or FAIL
    error_type: str = ""
    explanation: str = ""
    
    # Legacy fields to support Reporter without breaking everything
    outcome: AttackOutcome = AttackOutcome.ERROR
    expected: AttackOutcome = AttackOutcome.ERROR
    defense_layer: str = ""
    severity: Severity = Severity.NONE
    http_status: int = 0
    payment_call_count: int = 0
    payment_creation_count: int = 0
    transaction_id: str = ""
    evidence: str = ""
    actual: str = ""
    duration_ms: float = 0.0
    error: str = ""
    details: str = ""
    
    @property
    def passed(self) -> bool:
        return self.status == "PASS"
    
    @property
    def attack_id(self): return self.case_id

# Alias for backwards compatibility with runner/reporter types
AttackResult = EvaluationResult
