from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, Callable, Awaitable

class AttackOutcome(str, Enum):
    BLOCKED = "BLOCKED"
    DETECTED = "DETECTED"
    NOT_BLOCKED = "NOT_BLOCKED"
    ERROR = "ERROR"
    INCONCLUSIVE = "INCONCLUSIVE"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
@dataclass
class ExecutionResult:
    outcome: AttackOutcome
    http_status: int = 0
    error: str = ""
    payment_call_count: int = 0
    payment_creation_count: int = 0
    transaction_id: str = ""
    evidence: str = ""

@dataclass
class AttackDefinition:
    attack_id: str
    name: str
    category: str
    attacker: str
    preconditions: str
    malicious_input: str
    attack_path: str
    expected_security_property: str
    expected_result: AttackOutcome
    defense_layer: str
    severity: Severity
    # Function that takes an AsyncClient and returns an ExecutionResult
    execute: Callable[['httpx.AsyncClient'], Awaitable[ExecutionResult]]

@dataclass
class AttackResult:
    attack_id: str
    name: str
    category: str
    outcome: AttackOutcome
    expected: AttackOutcome
    defense_layer: str
    severity: Severity
    http_status: int = 0
    payment_call_count: int = 0
    payment_creation_count: int = 0
    transaction_id: str = ""
    evidence: str = ""
    actual: str = ""
    duration_ms: float = 0.0
    error: str = ""
    payment_call_count: int = 0
    payment_creation_count: int = 0
    transaction_id: str = ""
    evidence: str = ""
    details: str = ""
    
    @property
    def passed(self) -> bool:
        return self.outcome in (AttackOutcome.BLOCKED, AttackOutcome.DETECTED)

