package vilr.authorization
import rego.v1

default allow := false

policy_version := "v1"

allow if {
    count(violations) == 0
}

decision := {
    "allow": allow,
    "violations": violations,
    "policy_version": policy_version
}

# Ensure required fields are present
valid_input if {
    input.mandate
    input.cart
    input.semantic
    is_number(input.current_time)
}

violations contains {"code": "INVALID_INPUT", "message": "Missing required input fields"} if {
    not valid_input
}

# Expiration
violations contains {"code": "MANDATE_EXPIRED", "message": "Mandate is expired"} if {
    valid_input
    input.current_time >= input.mandate.exp
}

# Budget
violations contains {"code": "BUDGET_EXCEEDED", "message": "Cart total exceeds max amount"} if {
    valid_input
    to_number(input.cart.total_amount) > to_number(input.mandate.max_budget)
}

# Currency
violations contains {"code": "CURRENCY_MISMATCH", "message": "Currency does not match"} if {
    valid_input
    input.cart.currency != input.mandate.currency
}

# Merchant Allowed
violations contains {"code": "MERCHANT_NOT_ALLOWED", "message": "Merchant not in allowed list"} if {
    valid_input
    is_array(input.mandate.allowed_merchants)
    count(input.mandate.allowed_merchants) > 0
    not merchant_in_list(input.cart.merchant_id, input.mandate.allowed_merchants)
}

# Merchant Prohibited
violations contains {"code": "MERCHANT_PROHIBITED", "message": "Merchant is prohibited"} if {
    valid_input
    merchant_in_list(input.cart.merchant_id, input.mandate.prohibited_merchants)
}

# Category Allowed
violations contains {"code": "CATEGORY_NOT_ALLOWED", "message": "Category not in allowed list"} if {
    valid_input
    is_array(input.mandate.allowed_categories)
    count(input.mandate.allowed_categories) > 0
    not category_in_list(input.cart.category, input.mandate.allowed_categories)
}

# Category Prohibited
violations contains {"code": "CATEGORY_PROHIBITED", "message": "Category is prohibited"} if {
    valid_input
    category_in_list(input.cart.category, input.mandate.prohibited_categories)
}

# Semantic Fail
violations contains {"code": "SEMANTIC_FAIL", "message": "Semantic assessment failed"} if {
    valid_input
    input.semantic.status == "FAIL"
}

# Semantic Review
violations contains {"code": "SEMANTIC_REVIEW", "message": "Semantic assessment requires review"} if {
    valid_input
    input.semantic.status == "REVIEW"
}

# Helpers
merchant_in_list(m, lst) if {
    lst[_] == m
}

category_in_list(c, lst) if {
    lst[_] == c
}
