from app.domain.models import PolicyExplanation, AuthorizationDecision, PolicyMetadata
from typing import Dict, Any

class DeterministicPolicyExplainer:
    def __init__(self, metadata: PolicyMetadata):
        self.metadata = metadata

    def explain(self, decision: AuthorizationDecision, input_data: Dict[str, Any]) -> PolicyExplanation:
        if decision.allowed:
            return PolicyExplanation(
                policy_name=self.metadata.name,
                policy_version=self.metadata.version,
                decision="ALLOW",
                rule="default_allow",
                input_field="all",
                expected_value="pass",
                actual_value="pass",
                message="Transaction allowed by policy."
            )

        violation = decision.violations[0] if decision.violations else {"code": "UNKNOWN", "message": "Authorization denied by policy."}
        code = violation.get("code")
        
        rule = "unknown"
        expected = "unknown"
        actual = "unknown"
        field = "unknown"

        if code == "BUDGET_EXCEEDED":
            rule = "transaction.amount <= intent.max_amount"
            field = "cart.total_amount"
            expected = str(input_data.get("mandate", {}).get("max_amount"))
            actual = str(input_data.get("cart", {}).get("total_amount"))
        elif code == "CURRENCY_MISMATCH":
            rule = "cart.currency == intent.currency"
            field = "cart.currency"
            expected = str(input_data.get("mandate", {}).get("currency"))
            actual = str(input_data.get("cart", {}).get("currency"))
        elif code == "MANDATE_EXPIRED":
            rule = "current_time < intent.exp"
            field = "current_time"
            expected = str(input_data.get("mandate", {}).get("exp"))
            actual = str(input_data.get("current_time"))
        elif code == "MERCHANT_NOT_ALLOWED":
            rule = "merchant_id in allowed_merchants"
            field = "cart.merchant_id"
            expected = str(input_data.get("mandate", {}).get("allowed_merchants"))
            actual = str(input_data.get("cart", {}).get("merchant_id"))
        elif code == "MERCHANT_PROHIBITED":
            rule = "merchant_id not in prohibited_merchants"
            field = "cart.merchant_id"
            expected = "not in " + str(input_data.get("mandate", {}).get("prohibited_merchants"))
            actual = str(input_data.get("cart", {}).get("merchant_id"))
        elif code == "CATEGORY_NOT_ALLOWED":
            rule = "category in allowed_categories"
            field = "cart.category"
            expected = str(input_data.get("mandate", {}).get("allowed_categories"))
            actual = str(input_data.get("cart", {}).get("category"))
        elif code == "CATEGORY_PROHIBITED":
            rule = "category not in prohibited_categories"
            field = "cart.category"
            expected = "not in " + str(input_data.get("mandate", {}).get("prohibited_categories"))
            actual = str(input_data.get("cart", {}).get("category"))
        elif code == "SEMANTIC_FAIL":
            rule = "semantic.status != FAIL"
            field = "semantic.status"
            expected = "PASS or REVIEW"
            actual = str(input_data.get("semantic", {}).get("status"))
        elif code == "SEMANTIC_REVIEW":
            rule = "semantic.status != REVIEW"
            field = "semantic.status"
            expected = "PASS"
            actual = "REVIEW"

        return PolicyExplanation(
            policy_name=self.metadata.name,
            policy_version=self.metadata.version,
            decision="DENY",
            rule=rule,
            input_field=field,
            expected_value=expected,
            actual_value=actual,
            message=str(violation.get("message", "Authorization denied by policy."))
        )
