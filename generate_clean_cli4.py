with open("demo_template.txt", "r") as f:
    text = f.read()

import re

# Fix FakePolicy
fake_policy_new = """    class FakePolicy:
        async def evaluate(self, input_data):
            # dict structure: {"user_intent": {...}, "cart": {...}, "semantic_result": {...}}
            cart = input_data.get("cart", {})
            intent = input_data.get("user_intent", {})
            constraints = intent.get("hard_constraints", {})
            semantic = input_data.get("semantic_result", {})
            
            if float(cart.get("total_amount", 0)) > float(constraints.get("max_budget", 0)):
                return AuthorizationDecision(allowed=False, violations=[{"type":"budget", "message":"Exceeded budget"}], policy_version="1.0")
            if semantic.get("status") != "PASS":
                return AuthorizationDecision(allowed=False, violations=[{"type":"semantic", "message":"Semantic mismatch"}], policy_version="1.0")
            return AuthorizationDecision(allowed=True, violations=[], policy_version="1.0")
            
        def is_available(self):
            return True
"""

text = re.sub(r'    class FakePolicy:.*?        def is_available\(self\):\n            return True\n', fake_policy_new, text, flags=re.DOTALL)

with open("demo_template.txt", "w") as f:
    f.write(text)

