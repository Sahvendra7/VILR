import re
with open("tests/unit/test_tier2a_security_boundaries.py", "r") as f:
    content = f.read()

content = content.replace(
    "res = await verifier.verify(None, None)",
    """from app.domain.models import UserIntent, Cart, HardConstraints, SoftPreferences
    intent = UserIntent(user_id="1", raw_prompt="", semantic_intent="", hard_constraints=HardConstraints(max_budget=10, currency="INR"), soft_preferences=SoftPreferences())
    cart = Cart(items=[], total_amount=10, currency="INR", merchant_id="m1")
    res = await verifier.verify(intent, cart)"""
)

with open("tests/unit/test_tier2a_security_boundaries.py", "w") as f:
    f.write(content)
