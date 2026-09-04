from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.domain.models import UserIntent, Cart, AuditRecord, Identifier

class ErrorResponse(BaseModel):
    error: str
    message: str
    code: str

class IntentRequest(BaseModel):
    # Just a placeholder wrapper for UserIntent
    intent: UserIntent

class IntentResponse(BaseModel):
    status: str
    message: str

class AuthorizeRequest(BaseModel):
    transaction_id: Identifier
    open_checkout_token: str
    closed_checkout_token: str
    user_intent: UserIntent
    cart: Cart
    user_public_key: Dict[str, Any]
    merchant_public_key: Dict[str, Any]

class AuthorizeResponse(BaseModel):
    transaction_id: str
    status: str
    message: str
    reservation_status: Optional[str] = None
    execution_token: Optional[str] = None
    policy_version: Optional[str] = None

class ExecuteRequest(BaseModel):
    transaction_id: Identifier
    execution_token: str
    amount: Decimal
    currency: str
    merchant_id: str
    mandate_hash: str
    provider_idempotency_key: str
    payment_method_id: str

class ExecuteResponse(BaseModel):
    transaction_id: str
    status: str
    receipt: Optional[Dict[str, Any]] = None

class VerifyRequest(BaseModel):
    transaction_id: Identifier
    # Some proof elements

class VerifyResponse(BaseModel):
    transaction_id: str
    status: str
    isValid: bool
