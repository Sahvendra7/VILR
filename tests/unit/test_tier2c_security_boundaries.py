import pytest
from app.security.risk import DeterministicRiskCalculator

def test_risk_calculator_deterministic():
    calc = DeterministicRiskCalculator()
    
    # Empty signals
    res = calc.calculate_risk([])
    assert res.score == 0
    assert res.level == "LOW"
    
    # Semantic fail signal
    res = calc.calculate_risk(["SEMANTIC_FAIL"])
    assert res.score == 60
    assert res.level == "MEDIUM"
    
    # Critical signal
    res = calc.calculate_risk(["SIGNATURE_FAILURE"])
    assert res.score >= 100
    assert res.level == "CRITICAL"
    
    # Combined signals clamped
    res = calc.calculate_risk(["SIGNATURE_FAILURE", "REPLAY_DETECTED", "CART_MISMATCH"])
    assert res.score == 200 # clamped to 200
    assert res.level == "CRITICAL"

def test_risk_score_is_context_only():
    calc = DeterministicRiskCalculator()
    res = calc.calculate_risk(["CART_MISMATCH", "POLICY_VIOLATION"])
    
    # Assert risk model DOES NOT have an authorize method or decision field
    assert not hasattr(res, "authorize")
    assert not hasattr(res, "decision")
    assert not hasattr(res, "allowed")
    
    # Assert it only provides context
    assert res.level == "CRITICAL"
    assert res.score == 150
