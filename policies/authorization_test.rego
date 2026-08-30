package vilr.authorization
import rego.v1

# Helper to construct valid base input
base_input := {
    "mandate": {
        "exp": 2000,
        "max_amount": 50000.0,
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
    "current_time": 1000
}

test_allow_valid if {
    res := decision with input as base_input
    res.allow == true
    count(res.violations) == 0
}

test_deny_over_budget if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/cart/total_amount", "value": 50001.0}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "BUDGET_EXCEEDED"
}

test_allow_exact_budget if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/cart/total_amount", "value": 50000.0}])
    res := decision with input as inp
    res.allow == true
}

test_deny_currency_mismatch if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/cart/currency", "value": "USD"}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "CURRENCY_MISMATCH"
}

test_deny_merchant_not_allowed if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/cart/merchant_id", "value": "m2"}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "MERCHANT_NOT_ALLOWED"
}

test_deny_merchant_prohibited if {
    # Even if allowed list is empty, prohibited list must block
    inp := json.patch(base_input, [
        {"op": "replace", "path": "/cart/merchant_id", "value": "m3"},
        {"op": "replace", "path": "/mandate/allowed_merchants", "value": []}
    ])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "MERCHANT_PROHIBITED"
}

test_deny_category_not_allowed if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/cart/category", "value": "phone"}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "CATEGORY_NOT_ALLOWED"
}

test_deny_category_prohibited if {
    inp := json.patch(base_input, [
        {"op": "replace", "path": "/cart/category", "value": "gaming"},
        {"op": "replace", "path": "/mandate/allowed_categories", "value": []}
    ])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "CATEGORY_PROHIBITED"
}

test_deny_expired if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/current_time", "value": 2001}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "MANDATE_EXPIRED"
}

test_deny_expiration_boundary if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/current_time", "value": 2000}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "MANDATE_EXPIRED"
}

test_deny_missing_input if {
    res := decision with input as {}
    res.allow == false
    res.violations[_].code == "INVALID_INPUT"
}

test_deny_semantic_fail if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/semantic/status", "value": "FAIL"}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "SEMANTIC_FAIL"
}

test_deny_semantic_review if {
    inp := json.patch(base_input, [{"op": "replace", "path": "/semantic/status", "value": "REVIEW"}])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "SEMANTIC_REVIEW"
}

test_llm_cannot_override_budget if {
    inp := json.patch(base_input, [
        {"op": "replace", "path": "/cart/total_amount", "value": 100000.0},
        {"op": "replace", "path": "/semantic/confidence", "value": 0.999}
    ])
    res := decision with input as inp
    res.allow == false
    res.violations[_].code == "BUDGET_EXCEEDED"
}

test_multiple_violations if {
    inp := json.patch(base_input, [
        {"op": "replace", "path": "/cart/total_amount", "value": 100000.0},
        {"op": "replace", "path": "/cart/currency", "value": "USD"},
        {"op": "replace", "path": "/cart/merchant_id", "value": "m3"}
    ])
    res := decision with input as inp
    res.allow == false
    codes := {v.code | some v in res.violations}
    codes == {"BUDGET_EXCEEDED", "CURRENCY_MISMATCH", "MERCHANT_PROHIBITED", "MERCHANT_NOT_ALLOWED"}
}
