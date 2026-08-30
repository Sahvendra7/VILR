import pytest
from decimal import Decimal
from pydantic import ValidationError
from app.domain.models import (
    HardConstraints, UserIntent, CartItem, Cart, SemanticAssessment, ExecutionRequest, AuditRecord
)

def test_hard_constraints_valid():
    hc = HardConstraints(
        max_budget=Decimal("100.50"),
        currency="USD",
        allowed_merchants=["M123"]
    )
    assert hc.max_budget == Decimal("100.50")
    assert hc.currency == "USD"

def test_hard_constraints_invalid_currency():
    with pytest.raises(ValidationError):
        HardConstraints(max_budget=Decimal("100.00"), currency="us")

def test_hard_constraints_negative_budget():
    with pytest.raises(ValidationError):
        HardConstraints(max_budget=Decimal("-10.00"), currency="USD")

def test_user_intent_valid():
    hc = HardConstraints(max_budget=Decimal("50.00"), currency="EUR")
    ui = UserIntent(
        user_id="U1",
        raw_prompt="Buy a shoe",
        semantic_intent="shoe purchase",
        hard_constraints=hc,
        soft_preferences={"preferred_brands": ["Nike"]}
    )
    assert ui.user_id == "U1"

def test_cart_item_validation():
    # Negative quantity
    with pytest.raises(ValidationError):
        CartItem(item_id="I1", name="Shoe", quantity=-1, unit_price=Decimal("10"), currency="USD", category="apparel")
    
    # Negative price
    with pytest.raises(ValidationError):
        CartItem(item_id="I1", name="Shoe", quantity=1, unit_price=Decimal("-10"), currency="USD", category="apparel")
    
    # Valid
    c = CartItem(item_id="I1", name="Shoe", quantity=2, unit_price=Decimal("10"), currency="USD", category="apparel")
    assert c.quantity == 2

def test_semantic_assessment_confidence_bounds():
    with pytest.raises(ValidationError):
        SemanticAssessment(
            status="PASS", confidence=1.5, checks={}, violations=[], reasoning="test"
        )
    with pytest.raises(ValidationError):
        SemanticAssessment(
            status="PASS", confidence=-0.1, checks={}, violations=[], reasoning="test"
        )
    sa = SemanticAssessment(
        status="PASS", confidence=0.99, checks={}, violations=[], reasoning="test"
    )
    assert sa.confidence == 0.99
    
    with pytest.raises(ValidationError):
        SemanticAssessment(
            status="INVALID", confidence=0.9, checks={}, violations=[], reasoning="test"
        )

def test_missing_required_fields():
    with pytest.raises(ValidationError):
        UserIntent() # Missing everything

def test_execution_request_valid():
    er = ExecutionRequest(
        transaction_id="tx_123",
        idempotency_key="ik_456",
        merchant_id="m_789",
        amount=Decimal("10.00"),
        currency="USD",
        payment_method_id="pm_abc"
    )
    assert er.transaction_id == "tx_123"
    assert er.amount == Decimal("10.00")

def test_execution_request_invalid_currency():
    with pytest.raises(ValidationError):
        ExecutionRequest(
            transaction_id="tx_123",
            idempotency_key="ik_456",
            merchant_id="m_789",
            amount=Decimal("10.00"),
            currency="IN", # Invalid length
            payment_method_id="pm_abc"
        )

def test_audit_record_valid():
    from datetime import datetime
    ar = AuditRecord(
        transaction_id="tx_1",
        state="PAYMENT_CONFIRMED",
        decision="ALLOW",
        timestamps={"created": datetime.now()},
        open_mandate_hash="hash1",
        checkout_hash="hash2",
        current_record_hash="hash3"
    )
    assert ar.transaction_id == "tx_1"

def test_cart_valid():
    c = Cart(
        items=[
            CartItem(item_id="i1", name="Apple", quantity=1, unit_price=Decimal("1.50"), currency="USD", category="food")
        ],
        total_amount=Decimal("1.50"),
        currency="USD",
        merchant_id="m1"
    )
    assert c.total_amount == Decimal("1.50")
