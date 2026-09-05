from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Annotated, Dict, Any, Literal
from pydantic import BaseModel, Field, StringConstraints

# Core Types
CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Money = Annotated[Decimal, Field(ge=0)]
Identifier = Annotated[str, StringConstraints(min_length=1)]
Confidence = Annotated[float, Field(ge=0.0, le=1.0)]

class HardConstraints(BaseModel):
    max_budget: Money
    currency: CurrencyCode
    allowed_merchants: List[Identifier] = Field(default_factory=list)
    allowed_categories: List[str] = Field(default_factory=list)
    prohibited_merchants: List[Identifier] = Field(default_factory=list)
    prohibited_categories: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None

class SoftPreferences(BaseModel):
    preferred_brands: List[str] = Field(default_factory=list)
    prohibited_brands: List[str] = Field(default_factory=list)
    additional_instructions: str = ""

class UserIntent(BaseModel):
    user_id: Identifier
    raw_prompt: str
    semantic_intent: str
    hard_constraints: HardConstraints
    soft_preferences: SoftPreferences

class CartItem(BaseModel):
    item_id: Identifier
    name: str
    quantity: Annotated[int, Field(ge=0)]
    unit_price: Money
    currency: CurrencyCode
    category: str
    brand: Optional[str] = None

class Cart(BaseModel):
    items: List[CartItem]
    total_amount: Money
    currency: CurrencyCode
    merchant_id: Identifier

class MerchantOffer(BaseModel):
    merchant_id: Identifier
    cart: Cart
    # In AP2, the offer often contains the cryptographic elements to be signed.
    # For now, it wraps the cart and merchant ID.

class AgentIdentity(BaseModel):
    agent_id: Identifier
    public_key_jwk: Dict[str, Any]

class MerchantIdentity(BaseModel):
    merchant_id: Identifier
    public_key_jwk: Dict[str, Any]

# Mandates
class OpenCheckoutMandate(BaseModel):
    mandate_id: Identifier
    user_id: Identifier
    constraints: HardConstraints
    intent_hash: str
    signature: str

class OpenPaymentMandate(BaseModel):
    mandate_id: Identifier
    open_checkout_mandate_hash: str
    payment_method_id: Identifier
    signature: str

class ClosedCheckoutMandate(BaseModel):
    mandate_id: Identifier
    open_mandate_hash: str
    merchant_id: Identifier
    cart_hash: str
    signature: str

class ClosedPaymentMandate(BaseModel):
    mandate_id: Identifier
    closed_checkout_mandate_hash: str
    open_payment_mandate_hash: str
    signature: str

# Semantic Layer
class SemanticViolation(BaseModel):
    type: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    evidence: str

class SemanticAssessment(BaseModel):
    status: Literal["PASS", "REVIEW", "FAIL"]
    confidence: float = Field(ge=0.0, le=1.0)
    checks: Dict[str, bool] = Field(default_factory=dict)
    violations: List[SemanticViolation]
    reasoning: str

# Policy Engine
class AuthorizationDecision(BaseModel):
    allowed: bool
    violations: List[Dict[str, str]]
    policy_version: str
    policy_hash: str = ""

# Execution
class ExecutionRequest(BaseModel):
    transaction_id: Identifier
    idempotency_key: Identifier
    merchant_id: Identifier
    amount: Money
    currency: CurrencyCode
    payment_method_id: Identifier
    mandate_hash: str

class ExecutionReceipt(BaseModel):
    transaction_id: Identifier
    provider_transaction_id: Optional[str] = None
    status: Literal["SUCCESS", "FAILED", "UNKNOWN"]
    timestamp: datetime
    error_message: Optional[str] = None

# Audit
class AuditRecord(BaseModel):
    transaction_id: Identifier
    user_id: str
    agent_id: str
    merchant_id: str
    intent_hash: str
    open_mandate_hash: str
    cart_hash: str
    policy_decision: Optional[str] = None
    semantic_decision: Optional[str] = None
    semantic_confidence: Optional[float] = None
    authorization_status: Optional[str] = None
    timestamp: datetime
    nonce: str
    payment_attempt_id: Optional[str] = None
    execution_status: Optional[str] = None
    failure_reason: Optional[str] = None
    state: str
    prev_record_hash: str
    record_hash: str
    investigation: Optional[Dict[str, Any]] = None
    evidence: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    policy_metadata: Optional[Dict[str, str]] = None
class SecurityReceipt(BaseModel):
    receipt_id: str
    request_id: str
    intent_id: Optional[str] = None
    transaction_id: Optional[str] = None

    intent_verified: bool
    cryptographic_verification: bool
    cart_verified: bool

    replay_check: str

    semantic_result: Optional[str] = None
    policy_result: str
    execution_result: str

    execution_status: Optional[str] = None
    provider_call: Optional[str] = None
    provider_request_id: Optional[str] = None
    automatic_retry: Optional[str] = None
    reconciliation: Optional[str] = None

    final_decision: str

    decision_source: str
    explanation_source: Optional[str] = None

    policy_version: Optional[str] = None

    audit_event_id: Optional[str] = None
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None

    evidence: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None

    timestamp: datetime

class PolicyMetadata(BaseModel):
    name: str
    version: str
    hash: str

class IntentEvidence(BaseModel):
    intent_id: str
    intent_timestamp: datetime
    intent_status: str
    intent_hash: str

class CryptographicEvidence(BaseModel):
    signature_verified: bool
    intent_hash: str
    cart_hash: str
    transaction_binding: bool
    verification_result: str

class CartEvidence(BaseModel):
    expected_cart_hash: str
    actual_cart_hash: str
    cart_match: bool
    expected_amount: str
    actual_amount: str

class ReplayEvidence(BaseModel):
    idempotency_key: str
    replay_detected: bool
    reservation_status: str
    execution_token_status: str

class SemanticEvidence(BaseModel):
    semantic_result: str
    confidence: float
    detected_mismatches: List[str] = Field(default_factory=list)
    provider: str
    advisory_only: Literal[True] = True

class PolicyEvidence(BaseModel):
    policy_name: str
    policy_version: str
    policy_hash: str
    policy_decision: str
    matched_rules: List[str] = Field(default_factory=list)
    violations: List[Dict[str, str]] = Field(default_factory=list)

class ExecutionEvidence(BaseModel):
    execution_authorized: bool
    provider: str
    provider_request_id: Optional[str] = None
    execution_status: str

class DecisionEvidence(BaseModel):
    intent: IntentEvidence
    cryptographic: CryptographicEvidence
    cart: CartEvidence
    replay: ReplayEvidence
    semantic: Optional[SemanticEvidence] = None
    policy: PolicyEvidence
    execution: ExecutionEvidence
    evidence_hash: Optional[str] = None

class PolicyExplanation(BaseModel):
    policy_name: str
    policy_version: str
    decision: str
    rule: str
    input_field: str
    expected_value: str
    actual_value: str
    message: str
