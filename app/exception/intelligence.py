from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import json
import logging

logger = logging.getLogger(__name__)

class ExceptionCategory(str, Enum):
    CART_MISMATCH = "CART_MISMATCH"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    INTENT_MISMATCH = "INTENT_MISMATCH"
    REPLAY_ATTACK = "REPLAY_ATTACK"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    POLICY_DENIED = "POLICY_DENIED"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    EXPIRED_INTENT = "EXPIRED_INTENT"
    CRYPTOGRAPHIC_VERIFICATION_FAILURE = "CRYPTOGRAPHIC_VERIFICATION_FAILURE"
    SIGNATURE_VERIFICATION_FAILURE = "SIGNATURE_VERIFICATION_FAILURE"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    MALFORMED_REQUEST = "MALFORMED_REQUEST"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RecommendedAction(str, Enum):
    BLOCK = "BLOCK"
    REAUTHORIZE = "REAUTHORIZE"
    RETRY = "RETRY"
    INVESTIGATE = "INVESTIGATE"
    CONTACT_OPERATOR = "CONTACT_OPERATOR"
    RECONCILE = "RECONCILE"

class DecisionSource(str, Enum):
    CRYPTO = "CRYPTO"
    REDIS = "REDIS"
    OPA = "OPA"
    PROVIDER = "PROVIDER"
    SYSTEM = "SYSTEM"

class ExceptionInvestigation(BaseModel):
    category: ExceptionCategory
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]
    explanation: str
    recommended_action: RecommendedAction
    decision_source: DecisionSource

class InvestigationContext(BaseModel):
    request_id: str
    intent_id: Optional[str] = None
    transaction_id: Optional[str] = None
    workflow_state: str
    deterministic_decision: str
    failure_code: Optional[str] = None
    relevant_evidence: List[str] = Field(default_factory=list)
    policy_result: Optional[Dict[str, Any]] = None
    semantic_result: Optional[Dict[str, Any]] = None
    provider_result: Optional[Dict[str, Any]] = None

class ExceptionIntelligenceLayer:
    def __init__(self, llm_provider):
        self.llm = llm_provider

    async def investigate(self, context: InvestigationContext) -> ExceptionInvestigation:
        system_prompt = """You are the Exception Intelligence module for VILR.
You must analyze the failure context and provide a structured JSON response.
You have NO authorization authority.
Do NOT authorize or execute payments. Your role is purely advisory.
Return ONLY valid JSON matching the exact schema requested."""

        user_prompt = f"Analyze the following failure context:\\n{context.model_dump_json(indent=2)}\\n"

        try:
            # We enforce a hard schema requirement on the LLM
            response_json = await self.llm.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1024
            )

            investigation = ExceptionInvestigation.model_validate(response_json)
            return investigation

        except Exception as e:
            logger.error(f"Exception intelligence failed: {e}")
            return ExceptionInvestigation(
                category=ExceptionCategory.UNKNOWN_ERROR,
                severity=Severity.HIGH,
                confidence=1.0,
                evidence=[f"Investigation failed: {str(e)}", "Deterministic decision preserved."],
                explanation="Exception Intelligence was unavailable or returned an invalid schema. Defaulting to deterministic fallback.",
                recommended_action=RecommendedAction.BLOCK,
                decision_source=DecisionSource.SYSTEM
            )
