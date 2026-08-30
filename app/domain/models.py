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

# Execution
class ExecutionRequest(BaseModel):
    transaction_id: Identifier
    idempotency_key: Identifier
    merchant_id: Identifier
    amount: Money
    currency: CurrencyCode
    payment_method_id: Identifier

class ExecutionReceipt(BaseModel):
    transaction_id: Identifier
    provider_transaction_id: Optional[str] = None
    status: Literal["SUCCESS", "FAILED", "UNKNOWN"]
    timestamp: datetime
    error_message: Optional[str] = None

# Audit
class AuditRecord(BaseModel):
    transaction_id: Identifier
    state: str
    decision: str
    timestamps: Dict[str, datetime]
    open_mandate_hash: str
    checkout_hash: str
    prev_record_hash: Optional[str] = None
    current_record_hash: str
