import pytest
import time
from app.policy.engine import OPAPolicyEngine
from app.domain.errors import PolicyUnavailable

@pytest.fixture
def engine():
    return OPAPolicyEngine(opa_url="http://localhost:8181")

@pytest.fixture
def base_input():
    return {
        "mandate": {
            "exp": int(time.time()) + 3600,
            "max_budget": 50000.0,
            "currency": "INR",
            "allowed_merchants": ["m1"],
            "prohibited_merchants": ["m3"],
            "allowed_categories": ["laptop"],
            "prohibited_categories": ["gaming"]
        },
        "cart": {
            "merchant_id": "m1",
            "category": "laptop",
            "total_amount": 47999.0,
            "currency": "INR"
        },
        "semantic": {
            "status": "PASS",
            "confidence": 0.95
        },
        "current_time": int(time.time())
    }

@pytest.mark.asyncio
async def test_evaluate_allow(engine, base_input):
    decision = await engine.evaluate(base_input)
    assert decision.allowed == True
    assert len(decision.violations) == 0
    assert decision.policy_version == "v1"

@pytest.mark.asyncio
async def test_evaluate_deny_budget(engine, base_input):
    base_input["cart"]["total_amount"] = 60000.0
    decision = await engine.evaluate(base_input)
    assert decision.allowed == False
    assert any(v["code"] == "BUDGET_EXCEEDED" for v in decision.violations)

@pytest.mark.asyncio
async def test_evaluate_multiple_violations(engine, base_input):
    base_input["cart"]["total_amount"] = 60000.0
    base_input["cart"]["currency"] = "USD"
    decision = await engine.evaluate(base_input)
    assert decision.allowed == False
    codes = {v["code"] for v in decision.violations}
    assert "BUDGET_EXCEEDED" in codes
    assert "CURRENCY_MISMATCH" in codes

@pytest.mark.asyncio
async def test_security_llm_cannot_override_budget(engine, base_input):
    base_input["mandate"]["max_budget"] = 50000.0
    base_input["cart"]["total_amount"] = 100000.0
    base_input["semantic"]["status"] = "PASS"
    base_input["semantic"]["confidence"] = 0.999

    decision = await engine.evaluate(base_input)
    assert decision.allowed == False
    assert any(v["code"] == "BUDGET_EXCEEDED" for v in decision.violations)

@pytest.mark.asyncio
async def test_security_semantic_fail_causes_denial(engine, base_input):
    base_input["mandate"]["max_budget"] = 50000.0
    base_input["cart"]["total_amount"] = 40000.0
    base_input["semantic"]["status"] = "FAIL"
    base_input["semantic"]["confidence"] = 0.999

    decision = await engine.evaluate(base_input)
    assert decision.allowed == False
    assert any(v["code"] == "SEMANTIC_FAIL" for v in decision.violations)

@pytest.mark.asyncio
async def test_security_llm_cannot_override_merchant(engine, base_input):
    base_input["mandate"]["max_budget"] = 50000.0
    base_input["cart"]["total_amount"] = 40000.0
    base_input["cart"]["merchant_id"] = "m2" # not in allowed
    base_input["semantic"]["status"] = "PASS"

    decision = await engine.evaluate(base_input)
    assert decision.allowed == False
    assert any(v["code"] == "MERCHANT_NOT_ALLOWED" for v in decision.violations)

@pytest.mark.asyncio
async def test_engine_unavailable(base_input):
    bad_engine = OPAPolicyEngine(opa_url="http://localhost:9999", timeout=0.1)
    with pytest.raises(PolicyUnavailable):
        await bad_engine.evaluate(base_input)

@pytest.mark.asyncio
async def test_default_deny_malformed_input(engine):
    decision = await engine.evaluate({"invalid": "input"})
    assert decision.allowed == False

